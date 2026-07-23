from backend.filestore.local_filestore import LocalSQLiteFileStore
from backend.filestore.filestore import IngestableFile


def test_file_stored_properly(tmp_path):
    filestore = LocalSQLiteFileStore()
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        file_id = filestore.store(ingestable)

    assert file_id is not None


def test_file_retrieved_properly(tmp_path):
    filestore = LocalSQLiteFileStore()
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    with open(test_file, "rb") as f:
        ingestable = IngestableFile(f)
        file_id = filestore.store(ingestable)

    ingestable = filestore.get(file_id)

    assert type(ingestable) is IngestableFile
