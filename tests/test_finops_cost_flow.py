from app.Collectors.cost_collector import CostCollector
from app.agent.analyzers.cost_analyzer import CostAnalyzer
from dotenv import load_dotenv
import os


load_dotenv()

def test_finops_cost_pipeline():


    subscription_id = os.getenv(
        "AZURE_SUBSCRIPTION_ID"
    )


    collector = CostCollector()


    costs = collector.collect(
        subscription_id
    )


    print("\nCOST DATA")

    for c in costs:

        print(c)



    assert isinstance(
        costs,
        list
    )