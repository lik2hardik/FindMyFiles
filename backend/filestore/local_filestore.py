from .filestore import FileStore, IngestableFile
from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine, Session, text, select
import hashlib
import os
import shutil


class FileDB(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    original_name: str
    md5_name: str
    type: str | None = None
    date_added: datetime = Field(
        sa_column_kwargs={"server_default": text("(CURRENT_TIMESTAMP)")}
    )


def md5_hasher(file_obj):
    file_obj.seek(0)
    hasher = hashlib.md5()
    while chunk := file_obj.read(8192):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


class LocalSQLiteFileStore(FileStore):
    def __init__(self, path="backend/data"):
        super().__init__(path)

        DATABASE_URL = f"sqlite:///{os.path.join(self.path, 'file_metadata.db')}"
        os.makedirs(self.path, exist_ok=True)

        self.engine = create_engine(DATABASE_URL, echo=True)

        SQLModel.metadata.create_all(self.engine)

    def get(self, id):
        with Session(self.engine) as session:
            statement = select(FileDB).where(FileDB.id == id)
            file_row = session.exec(statement).one_or_none()

            if not file_row:
                raise FileNotFoundError(f"No file entry found in database for ID: {id}")

            os.makedirs(self.path, exist_ok=True)
            file_path = os.path.join(self.path, f"{file_row.md5_name}.{file_row.type}")

            if os.path.exists(file_path):
                f = open(file_path, "rb")
                return IngestableFile(file_obj=f, name=file_row.original_name)
            else:
                raise IOError(
                    f"Database ledger record found, but raw file was deleted from disk space: {file_path}"
                )

    def store(self, file: IngestableFile):
        file.file_obj.seek(0)

        md5_name = md5_hasher(file.file_obj)
        file_type = file.extension if file.extension else "txt"

        # store metadata in database
        file_row = FileDB(
            original_name=file.file_name,
            md5_name=md5_name,
            type=file_type,
        )

        file.file_obj.seek(0)

        with Session(self.engine) as session:
            try:
                session.add(file_row)

                # store file in data folder
                os.makedirs(self.path, exist_ok=True)
                file_path = os.path.join(
                    self.path, f"{file_row.md5_name}.{file_row.type}"
                )

                file.file_obj.seek(0)

                with open(file_path, "wb") as f_out:
                    shutil.copyfileobj(file.file_obj, f_out)

                session.commit()
                session.refresh(file_row)

                return file_row.id

            except Exception as e:
                session.rollback()
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise IOError(
                    f"Database/Disk atomic operations sync failed: {e}"
                ) from e
