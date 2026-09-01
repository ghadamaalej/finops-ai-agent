from app.services.execution.base_executor import BaseExecutor

class StorageExecutor(BaseExecutor):
    def __init__(self, storage_client, dry_run: bool = True):

        super().__init__(dry_run=dry_run)
        self.storage_client = storage_client
    
    async def execute(self, request):
        await self.validate(request)  
        
        if self.dry_run or request.dry_run:
            return self.dry_run_result(request)
        
        return {
            "status": "not implemented",
            "message": "Storage execution not yet implemented"
        }