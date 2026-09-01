from pydantic import BaseModel


class VerificationReport(BaseModel):


    total_expected_savings:float=0


    total_realized_savings:float=0


    success_rate:float=0


    overall_status:str


    resource_results:list=[]