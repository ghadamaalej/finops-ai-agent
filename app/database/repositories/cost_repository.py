
from datetime import datetime

from app.database.models import CostHistory



class CostRepository:


    def save_costs(
        self,
        db,
        subscription_id: str,
        costs: list[dict],
        *,
        collected_at: datetime | None = None,
        commit: bool = True,
    ):


        records=[]


        for cost in costs:


            records.append(

                CostHistory(

                    subscription_id=subscription_id,

                    resource_id=
                    cost["resource_id"],


                    resource_name=
                    cost.get("resource_name"),


                    service_name=
                    cost.get("service_name"),

                    daily_cost=cost.get("daily_cost"),


                    monthly_cost=cost.get("monthly_cost"),


                    currency=
                    cost.get("currency"),

                    cost_source=cost.get("cost_source"),
                    cost_type=cost.get("cost_type"),
                    is_estimated=cost.get("is_estimated"),
                    cost_status=cost.get("cost_status"),
                    collected_at=collected_at or datetime.utcnow(),

                )

            )


        if records:
            db.add_all(records)

        if commit:
            db.commit()

        return records
