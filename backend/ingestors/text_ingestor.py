from ingestor import  Ingestor,IngestableFile

class TextIngestor(Ingestor):
    def __init__(self, type="text", accepted_format=["txt"], name="default text"):
        return super().__init__(type, accepted_format, name)
    
    async def extract_text(self, file:IngestableFile):
        
        if file.extension not in self.accepted_format:
            raise TypeError(f"{file.extension} does not match any type in {self.accepted_format}") 

        file.file_obj.seek(0)
        data = file.file_obj.read()
        if isinstance(data, bytes):
            return data.decode('utf-8', errors='ignore')
        return data

