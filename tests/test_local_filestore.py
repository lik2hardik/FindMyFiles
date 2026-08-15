import os
from datetime import datetime

import pytest
from sqlmodel import Session, select

import backend.filestore.local_filestore as m
from backend.filestore.base_filestore import FileStoreError, IngestableFile
from backend.filestore.local_filestore import (
    DataNotFoundError,
    FileDB,
    LocalSQLiteFileStore,
)

"""Comprehensive unit tests for LocalSQLiteFileStore.

Covers every public operation (store, get, get_metadata, init) plus all
error-handling paths introduced by the error-handling review:
wrapped exceptions, exception chaining, rollback/cleanup guarantees,
and the file_path NameError regression.
"""


@pytest.fixture
def filestore(tmp_path):
    """A LocalSQLiteFileStore backed by a fresh tmp_path directory, so no
    test touches the real backend/data directory."""
    return LocalSQLiteFileStore(path=str(tmp_path / "fs"))


def open_ingestable(tmp_path, name, data):
    """Write `data` to a temp file named `name` and return an open read handle."""
    path = tmp_path / name
    path.write_bytes(data)
    return open(path, "rb")


def stored_row(session, file_id):
    """Fetch the FileDB row for `file_id` from the given session."""
    return session.get(FileDB, file_id)


class TestStore:
    def test_store_returns_id_and_persists_metadata(self, filestore, tmp_path):
        """store() returns an int id and persists original_name, md5_name,
        lowercase type, size, and a datetime date_added in the DB."""
        with open_ingestable(tmp_path, "report.pdf", b"%PDF-1.4 fake") as f:
            file_id = filestore.store(IngestableFile(f, name="report.pdf"))

        assert isinstance(file_id, int)

        with Session(filestore.engine) as session:
            row = stored_row(session, file_id)

        assert row.original_name == "report.pdf"
        assert row.md5_name == "307ddb5f41f66df59f1e28b325a31c3e"
        assert row.type == "pdf"
        assert row.size == len(b"%PDF-1.4 fake")
        assert isinstance(row.date_added, datetime)

    def test_store_writes_file_to_disk_with_md5_name(self, filestore, tmp_path):
        """store() writes the raw bytes to disk as {md5}.{type}."""
        data = b"hello world"
        with open_ingestable(tmp_path, "note.txt", data) as f:
            file_id = filestore.store(IngestableFile(f))

        with Session(filestore.engine) as session:
            row = stored_row(session, file_id)

        disk_path = os.path.join(filestore.path, f"{row.md5_name}.{row.type}")
        assert os.path.exists(disk_path)
        with open(disk_path, "rb") as f:
            assert f.read() == data

    def test_store_same_content_twice_creates_two_ids_same_file(self, filestore, tmp_path):
        """No dedup: identical content gets distinct ids but a shared md5-named
        disk file; both ids still retrieve the content."""
        data = b"duplicated"
        with open_ingestable(tmp_path, "a.txt", data) as f:
            id1 = filestore.store(IngestableFile(f))
        with open_ingestable(tmp_path, "b.txt", data) as f:
            id2 = filestore.store(IngestableFile(f))

        assert id1 != id2
        assert filestore.get(id1).file_obj.read() == data
        assert filestore.get(id2).file_obj.read() == data
        filestore.get(id1).file_obj.close()
        filestore.get(id2).file_obj.close()

    def test_store_extensionless_file_gets_unknown_type(self, filestore, tmp_path):
        """A file with no suffix is stored with type 'unknown' (the 'txt'
        fallback in store() is unreachable because IngestableFile always sets
        an extension)."""
        with open_ingestable(tmp_path, "README", b"content") as f:
            file_id = filestore.store(IngestableFile(f))

        with Session(filestore.engine) as session:
            row = stored_row(session, file_id)

        assert row.type == "unknown"
        assert os.path.exists(os.path.join(filestore.path, f"{row.md5_name}.unknown"))

    def test_store_empty_file(self, filestore, tmp_path):
        """A 0-byte file stores successfully with size 0 and the well-known
        md5 of the empty string."""
        with open_ingestable(tmp_path, "empty.txt", b"") as f:
            file_id = filestore.store(IngestableFile(f))

        with Session(filestore.engine) as session:
            row = stored_row(session, file_id)

        assert row.size == 0
        assert row.md5_name == "d41d8cd98f00b204e9800998ecf8427e"

    def test_store_md5_hash_failure_raises_filestore_error(self, filestore, tmp_path, monkeypatch):
        """A source-stream read failure during hashing raises FileStoreError
        with 'Failed to compute MD5 hash' and chains the original error."""
        def failing_hasher(file_obj):
            raise OSError("read failure")

        monkeypatch.setattr(m, "md5_hasher", failing_hasher)

        with open_ingestable(tmp_path, "a.txt", b"x") as f:
            with pytest.raises(FileStoreError, match="Failed to compute MD5 hash") as exc:
                filestore.store(IngestableFile(f))

        assert isinstance(exc.value.__cause__, OSError)

    def test_store_failure_before_file_path_assignment(self, filestore, tmp_path, monkeypatch):
        """Regression: a failure before file_path is assigned (e.g. os.makedirs
        raising) must not NameError in the except handler; it raises a chained
        FileStoreError, leaves no partial file, and rolls back the DB row."""
        def failing_makedirs(path, exist_ok=False):
            raise PermissionError("denied")

        monkeypatch.setattr(m.os, "makedirs", failing_makedirs)

        with open_ingestable(tmp_path, "a.txt", b"x") as f:
            with pytest.raises(FileStoreError) as exc:
                filestore.store(IngestableFile(f))

        assert isinstance(exc.value.__cause__, PermissionError)
        assert os.listdir(filestore.path) == ["file_metadata.db"]
        with Session(filestore.engine) as session:
            assert session.exec(select(FileDB)).all() == []

    def test_store_disk_write_failure_cleans_up_partial_file(self, filestore, tmp_path, monkeypatch):
        """A disk write failure removes the partially-written file and rolls
        back the DB row, so no partial state survives."""
        def failing_copyfileobj(src, dst):
            raise OSError("disk full")

        monkeypatch.setattr(m.shutil, "copyfileobj", failing_copyfileobj)

        with open_ingestable(tmp_path, "a.txt", b"x") as f:
            with pytest.raises(FileStoreError, match="Database/Disk") as exc:
                filestore.store(IngestableFile(f))

        assert isinstance(exc.value.__cause__, OSError)
        assert os.listdir(filestore.path) == ["file_metadata.db"]
        with Session(filestore.engine) as session:
            assert session.exec(select(FileDB)).all() == []

    def test_store_commit_failure_removes_disk_file(self, filestore, tmp_path, monkeypatch):
        """A DB commit failure removes the already-written disk file and leaves
        no DB row, keeping DB and disk consistent."""
        def failing_commit(self):
            raise RuntimeError("commit failed")

        monkeypatch.setattr(Session, "commit", failing_commit)

        with open_ingestable(tmp_path, "a.txt", b"x") as f:
            with pytest.raises(FileStoreError, match="Database/Disk") as exc:
                filestore.store(IngestableFile(f))

        assert isinstance(exc.value.__cause__, RuntimeError)
        assert os.listdir(filestore.path) == ["file_metadata.db"]
        with Session(filestore.engine) as session:
            assert session.exec(select(FileDB)).all() == []

    def test_store_cleanup_remove_failure_reports_cleanup_error(self, filestore, tmp_path, monkeypatch):
        """When cleanup os.remove itself fails, the error is reported as a
        FileStoreError ('Failed to remove file from disk') chained to the
        cleanup failure, not the original write failure."""
        def failing_copyfileobj(src, dst):
            raise OSError("disk full")

        def failing_remove(path):
            raise PermissionError("cannot remove")

        monkeypatch.setattr(m.shutil, "copyfileobj", failing_copyfileobj)
        monkeypatch.setattr(m.os, "remove", failing_remove)

        with open_ingestable(tmp_path, "a.txt", b"x") as f:
            with pytest.raises(
                FileStoreError, match="Failed to remove file from disk"
            ) as exc:
                filestore.store(IngestableFile(f))

        assert isinstance(exc.value.__cause__, PermissionError)
        with Session(filestore.engine) as session:
            assert session.exec(select(FileDB)).all() == []


class TestGet:
    def test_get_returns_matching_ingestable_file(self, filestore, tmp_path):
        """get() returns an IngestableFile with the original name, extension,
        and exact stored bytes."""
        data = b"retrieval check"
        with open_ingestable(tmp_path, "doc.txt", data) as f:
            file_id = filestore.store(IngestableFile(f, name="doc.txt"))

        ingestable = filestore.get(file_id)

        try:
            assert type(ingestable) is IngestableFile
            assert ingestable.file_name == "doc.txt"
            assert ingestable.extension == "txt"
            assert ingestable.file_obj.read() == data
        finally:
            ingestable.file_obj.close()

    def test_get_missing_id_raises_data_not_found(self, filestore):
        """get() on an unknown id raises DataNotFoundError mentioning the id."""
        with pytest.raises(DataNotFoundError, match="ID: 999"):
            filestore.get(999)

    def test_get_missing_disk_file_raises_filestore_error(self, filestore, tmp_path):
        """A DB row whose raw file was deleted raises a chained FileStoreError
        ('Failed to open file from disk') instead of a raw FileNotFoundError."""
        with open_ingestable(tmp_path, "doc.txt", b"x") as f:
            file_id = filestore.store(IngestableFile(f))

        with Session(filestore.engine) as session:
            row = stored_row(session, file_id)
            disk_path = os.path.join(filestore.path, f"{row.md5_name}.{row.type}")

        os.remove(disk_path)

        with pytest.raises(
            FileStoreError, match="Failed to open file from disk"
        ) as exc:
            filestore.get(file_id)

        assert isinstance(exc.value.__cause__, FileNotFoundError)

    def test_get_with_null_type_resolves_unknown_extension(self, filestore, tmp_path):
        """A row with type=NULL resolves its disk path as {md5}.unknown and
        still opens the file."""
        with open_ingestable(tmp_path, "doc.txt", b"x") as f:
            file_id = filestore.store(IngestableFile(f))

        with Session(filestore.engine) as session:
            row = stored_row(session, file_id)
            md5_name = row.md5_name
            row.type = None
            session.add(row)
            session.commit()
            os.rename(
                os.path.join(filestore.path, f"{md5_name}.txt"),
                os.path.join(filestore.path, f"{md5_name}.unknown"),
            )

        ingestable = filestore.get(file_id)
        try:
            assert ingestable.file_obj.read() == b"x"
        finally:
            ingestable.file_obj.close()

    @pytest.mark.skipif(os.geteuid() == 0, reason="root bypasses file permissions")
    def test_get_unreadable_file_raises_filestore_error(self, filestore, tmp_path):
        """An unreadable file (mode 000) surfaces as FileStoreError, not a raw
        PermissionError."""
        with open_ingestable(tmp_path, "doc.txt", b"x") as f:
            file_id = filestore.store(IngestableFile(f))

        with Session(filestore.engine) as session:
            row = stored_row(session, file_id)
            disk_path = os.path.join(filestore.path, f"{row.md5_name}.{row.type}")

        os.chmod(disk_path, 0)
        try:
            with pytest.raises(FileStoreError, match="Failed to open file from disk"):
                filestore.get(file_id)
        finally:
            os.chmod(disk_path, 0o644)


class TestGetMetadata:
    def test_get_metadata_returns_full_record(self, filestore, tmp_path):
        """get_metadata() returns all six fields with correct values, and
        date_added is a datetime."""
        data = b"metadata payload"
        with open_ingestable(tmp_path, "meta.pdf", data) as f:
            file_id = filestore.store(IngestableFile(f, name="meta.pdf"))

        metadata = filestore.get_metadata(file_id)

        assert metadata["file_id"] == file_id
        assert metadata["file_name"] == "meta.pdf"
        assert metadata["md5_name"]
        assert metadata["type"] == "pdf"
        assert metadata["size"] == len(data)
        assert isinstance(metadata["date_added"], datetime)

    def test_get_metadata_missing_id_raises_data_not_found(self, filestore):
        """get_metadata() on an unknown id raises DataNotFoundError mentioning
        the id."""
        with pytest.raises(DataNotFoundError, match="ID: 123"):
            filestore.get_metadata(123)


class TestInit:
    def test_init_creates_directory_and_database(self, tmp_path):
        """__init__ creates the storage directory and file_metadata.db at the
        given path."""
        store_path = tmp_path / "custom"
        LocalSQLiteFileStore(path=str(store_path))

        assert os.path.exists(store_path)
        assert os.path.exists(os.path.join(store_path, "file_metadata.db"))

    def test_init_with_unwritable_path_raises_filestore_error(self, tmp_path):
        """An unusable path (a file in the way) raises a chained FileStoreError
        instead of leaking the raw OSError."""
        blocker = tmp_path / "blocker"
        blocker.write_text("not a dir")

        with pytest.raises(FileStoreError, match="Failed to create/initialize") as exc:
            LocalSQLiteFileStore(path=str(blocker / "sub"))

        assert isinstance(exc.value.__cause__, OSError)


class TestContracts:
    def test_data_not_found_error_is_filestore_error(self):
        """DataNotFoundError must be a FileStoreError so a single catch-all
        handles every filestore failure."""
        assert issubclass(DataNotFoundError, FileStoreError)

    def test_ingestable_file_rejects_non_file_object(self):
        """IngestableFile rejects non-IOBase objects with FileStoreError."""
        with pytest.raises(FileStoreError):
            IngestableFile(file_obj=object())

    def test_all_store_errors_are_filestore_errors(self, filestore, tmp_path, monkeypatch):
        """Contract check: even a failing store() surfaces as FileStoreError,
        never a raw builtin exception."""
        def failing_makedirs(path, exist_ok=False):
            raise PermissionError("x")

        monkeypatch.setattr(m.os, "makedirs", failing_makedirs)

        with open_ingestable(tmp_path, "a.txt", b"x") as f:
            with pytest.raises(FileStoreError):
                filestore.store(IngestableFile(f))
