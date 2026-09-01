import numpy as np

from sklearn.linear_model import LinearRegression


class CostForecaster:

    def predict_next_month(self, history):

        if len(history) < 2:

            return {
                "predicted_next_month_cost": 0,
                "confidence": 0
            }


        X = np.array(
            [
                i
                for i in range(len(history))
            ]
        ).reshape(-1, 1)


        y = np.array(
            [
                float(h.monthly_cost)
                for h in history
            ]
        )


        model = LinearRegression()

        model.fit(
            X,
            y
        )


        next_month = np.array(
            [len(history)]
        ).reshape(-1, 1)


        prediction = model.predict(
            next_month
        )[0]


        prediction = max(
            0.0,
            float(prediction)
        )


        r2 = model.score(
            X,
            y
        )


        confidence = max(
            0.0,
            min(
                float(r2),
                1.0
            )
        )


        return {

            "predicted_next_month_cost":
                round(prediction, 2),

            "confidence":
                round(confidence, 2)

        }