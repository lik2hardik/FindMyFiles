class Ingestor:
    def __init(self,type = None,accepted_format = None,name = "default"):
        self.name = name
        self.type = type
        self.format = accepted_format
    
    async def extract_text(self,media) -> str:
        '''
        Given the media object, extract the relevant text.
        '''
        pass
