class AnalyticsExplainer:
    """
    Explains existing analytics data in plain language.
    Does NOT compute new metrics.
    """

    def explain(self, metric_name, data):
        if not data:
            return "📊 No data available to explain."

        return f"📊 Analytics Explanation:\n{self._basic_explanation(metric_name, data)}"

    def _basic_explanation(self, metric_name, data):
        # Safe, generic explanations
        if isinstance(data, (int, float)):
            return f"The current value of {metric_name} is {data}."
        if isinstance(data, dict):
            lines = []
            for k, v in data.items():
                lines.append(f"- {k}: {v}")
            return "Here is a breakdown:\n" + "\n".join(lines)
        return "This metric shows recent system performance."


# Single shared instance
analytics_explainer = AnalyticsExplainer()


