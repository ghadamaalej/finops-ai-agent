class FinancialVerifier:



    def verify(
        self,
        recommendation,
        before_cost,
        after_cost
    ):


        expected = (
            recommendation.estimated_savings
        )


        realized = (
            before_cost-after_cost
        )



        return {

            "expected_savings":
                expected,


            "realized_savings":
                round(realized,2),


            "success":
                realized >= expected*0.8

        }