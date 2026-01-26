"""
Databricks Agent for Approval Optimization

An AI agent that provides intelligent recommendations for improving
payment approval rates using natural language interaction.
"""

from databricks import agents
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
import yaml
import json


class ApprovalOptimizerAgent:
    """
    Databricks Agent for payment approval optimization
    
    This agent can:
    - Analyze decline patterns and suggest improvements
    - Recommend optimal payment solutions for specific scenarios
    - Provide retry timing recommendations
    - Generate actionable insights from transaction data
    """
    
    def __init__(self, config_path: str = "../config/app_config.yaml"):
        """Initialize the agent with configuration"""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.agent_config = self.config['agent']
        self.workspace = WorkspaceClient()
        
        # System prompt for the agent
        self.system_prompt = self.agent_config['system_prompt']
        
        # Tools available to the agent
        self.tools = [
            {
                "name": "get_approval_metrics",
                "description": "Get current approval rate metrics and trends",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_period": {
                            "type": "string",
                            "description": "Time period for metrics (e.g., '7d', '30d', '90d')"
                        },
                        "geography": {
                            "type": "string",
                            "description": "Optional geography filter"
                        }
                    },
                    "required": ["time_period"]
                }
            },
            {
                "name": "analyze_decline_reasons",
                "description": "Analyze decline reasons and identify patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "decline_reason_code": {
                            "type": "string",
                            "description": "Optional specific decline reason code to analyze"
                        },
                        "min_count": {
                            "type": "integer",
                            "description": "Minimum number of occurrences to include"
                        }
                    }
                }
            },
            {
                "name": "recommend_payment_solution",
                "description": "Recommend optimal payment solution for a transaction scenario",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "Transaction amount"
                        },
                        "geography": {
                            "type": "string",
                            "description": "Transaction geography"
                        },
                        "merchant_category": {
                            "type": "string",
                            "description": "Merchant category"
                        },
                        "risk_score": {
                            "type": "number",
                            "description": "Composite risk score (0-100)"
                        }
                    },
                    "required": ["amount", "geography"]
                }
            },
            {
                "name": "get_retry_recommendation",
                "description": "Get smart retry recommendation for a declined transaction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "decline_reason_code": {
                            "type": "string",
                            "description": "Decline reason code"
                        },
                        "retry_attempt": {
                            "type": "integer",
                            "description": "Current retry attempt number"
                        },
                        "hours_since_decline": {
                            "type": "number",
                            "description": "Hours since original decline"
                        }
                    },
                    "required": ["decline_reason_code", "retry_attempt"]
                }
            },
            {
                "name": "calculate_roi",
                "description": "Calculate ROI for implementing optimization strategies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "monthly_volume": {
                            "type": "integer",
                            "description": "Monthly transaction volume"
                        },
                        "avg_transaction_value": {
                            "type": "number",
                            "description": "Average transaction value"
                        },
                        "current_approval_rate": {
                            "type": "number",
                            "description": "Current approval rate (0-1)"
                        }
                    },
                    "required": ["monthly_volume", "avg_transaction_value", "current_approval_rate"]
                }
            }
        ]
    
    def get_approval_metrics(self, time_period: str = "7d", geography: str = None) -> dict:
        """Get approval metrics from the data warehouse"""
        # This would query the actual Delta tables
        # For demo purposes, returning mock data
        
        metrics = {
            "time_period": time_period,
            "geography": geography or "ALL",
            "total_transactions": 500000,
            "approved_transactions": 435000,
            "approval_rate": 0.87,
            "avg_amount": 125.50,
            "trend": "+2.3% vs previous period",
            "top_performing_solution": "NetworkToken (95% approval rate)",
            "improvement_opportunity": "8-12% potential improvement with smart routing"
        }
        
        return metrics
    
    def analyze_decline_reasons(self, decline_reason_code: str = None, min_count: int = 100) -> dict:
        """Analyze decline reasons and patterns"""
        
        if decline_reason_code:
            # Specific decline reason analysis
            analysis = {
                "decline_reason_code": decline_reason_code,
                "count": 15000,
                "percentage": 20.5,
                "avg_amount": 145.30,
                "top_geography": "LATAM",
                "recoverable": True,
                "recovery_rate": 0.35,
                "recommended_action": self._get_action_for_decline_reason(decline_reason_code)
            }
        else:
            # Overall decline analysis
            analysis = {
                "total_declines": 75234,
                "decline_rate": 0.148,
                "top_reasons": [
                    {"code": "51", "description": "Insufficient Funds", "count": 26500, "recoverable": True},
                    {"code": "05", "description": "Do Not Honor", "count": 15000, "recoverable": False},
                    {"code": "59", "description": "Suspected Fraud", "count": 12000, "recoverable": False},
                    {"code": "54", "description": "Expired Card", "count": 8500, "recoverable": True},
                    {"code": "61", "description": "Exceeds Limit", "count": 7234, "recoverable": True}
                ],
                "recoverable_percentage": 69.3,
                "estimated_recovery_value": 1250000
            }
        
        return analysis
    
    def recommend_payment_solution(
        self,
        amount: float,
        geography: str,
        merchant_category: str = None,
        risk_score: float = None
    ) -> dict:
        """Recommend optimal payment solution"""
        
        solutions = []
        
        # Rule-based recommendation logic
        if amount > 500 or (risk_score and risk_score > 50):
            solutions.append({
                "solution": "3DS",
                "reason": "High-value or high-risk transaction",
                "expected_approval_lift": 0.05,
                "cost": 0.15
            })
        
        if risk_score and risk_score < 30:
            solutions.append({
                "solution": "NetworkToken",
                "reason": "Low-risk transaction with high success rate",
                "expected_approval_lift": 0.15,
                "cost": 0.25
            })
        
        if amount > 1000:
            solutions.append({
                "solution": "IDPay",
                "reason": "High-value transaction benefits from identity verification",
                "expected_approval_lift": 0.12,
                "cost": 0.20
            })
        
        if geography in ["LATAM", "APAC"]:
            solutions.append({
                "solution": "Antifraud",
                "reason": "Higher fraud risk in this geography",
                "expected_approval_lift": 0.08,
                "cost": 0.10
            })
        
        if not solutions:
            solutions.append({
                "solution": "DataShareOnly",
                "reason": "Standard processing sufficient",
                "expected_approval_lift": 0.03,
                "cost": 0.05
            })
        
        # Calculate optimal combination
        total_lift = sum(s["expected_approval_lift"] for s in solutions)
        total_cost = sum(s["cost"] for s in solutions)
        
        recommendation = {
            "recommended_solutions": [s["solution"] for s in solutions],
            "details": solutions,
            "expected_total_lift": round(total_lift, 3),
            "total_cost": round(total_cost, 2),
            "roi": round((total_lift * amount) / total_cost, 2) if total_cost > 0 else 0
        }
        
        return recommendation
    
    def get_retry_recommendation(
        self,
        decline_reason_code: str,
        retry_attempt: int,
        hours_since_decline: float = 0
    ) -> dict:
        """Get smart retry recommendation"""
        
        # Fraud-related declines
        if decline_reason_code in ["41", "43", "59", "63"]:
            return {
                "should_retry": False,
                "reason": "Fraud-related decline - do not retry",
                "recommended_delay_hours": None,
                "expected_success_rate": 0.05
            }
        
        # Expired card
        if decline_reason_code == "54":
            return {
                "should_retry": False,
                "reason": "Expired card - requires card update via Account Updater",
                "recommended_delay_hours": None,
                "expected_success_rate": 0.10,
                "alternative_action": "Trigger Account Updater service"
            }
        
        # Maximum attempts
        if retry_attempt >= 3:
            return {
                "should_retry": False,
                "reason": "Maximum retry attempts reached",
                "recommended_delay_hours": None,
                "expected_success_rate": 0.15
            }
        
        # Insufficient funds
        if decline_reason_code == "51":
            if hours_since_decline < 24:
                return {
                    "should_retry": True,
                    "reason": "Insufficient funds - optimal retry window approaching",
                    "recommended_delay_hours": 24,
                    "expected_success_rate": 0.65,
                    "best_time": "24-72 hours after decline"
                }
            elif hours_since_decline < 72:
                return {
                    "should_retry": True,
                    "reason": "Insufficient funds - in optimal retry window",
                    "recommended_delay_hours": 0,
                    "expected_success_rate": 0.65
                }
            else:
                return {
                    "should_retry": True,
                    "reason": "Insufficient funds - past optimal window",
                    "recommended_delay_hours": 0,
                    "expected_success_rate": 0.40
                }
        
        # Limit exceeded
        if decline_reason_code in ["61", "65"]:
            return {
                "should_retry": True,
                "reason": "Limit exceeded - retry after reset period",
                "recommended_delay_hours": 24,
                "expected_success_rate": 0.55,
                "alternative_action": "Offer split payment option"
            }
        
        # Default recommendation
        return {
            "should_retry": True,
            "reason": "Standard retry with moderate success probability",
            "recommended_delay_hours": 24,
            "expected_success_rate": 0.35
        }
    
    def calculate_roi(
        self,
        monthly_volume: int,
        avg_transaction_value: float,
        current_approval_rate: float
    ) -> dict:
        """Calculate ROI for optimization strategies"""
        
        # Estimated improvements
        smart_checkout_improvement = 0.08  # 8%
        smart_retry_improvement = 0.03  # 3%
        total_improvement = smart_checkout_improvement + smart_retry_improvement
        
        # Calculate impact
        new_approval_rate = min(0.99, current_approval_rate + total_improvement)
        additional_approvals_monthly = monthly_volume * total_improvement
        additional_revenue_monthly = additional_approvals_monthly * avg_transaction_value
        annual_revenue = additional_revenue_monthly * 12
        
        # Costs (estimated)
        implementation_cost = 50000  # One-time
        monthly_operational_cost = 5000
        annual_operational_cost = monthly_operational_cost * 12
        
        # ROI calculation
        first_year_revenue = annual_revenue
        first_year_cost = implementation_cost + annual_operational_cost
        first_year_roi = ((first_year_revenue - first_year_cost) / first_year_cost) * 100
        
        payback_months = implementation_cost / (additional_revenue_monthly - monthly_operational_cost)
        
        return {
            "current_approval_rate": current_approval_rate,
            "projected_approval_rate": new_approval_rate,
            "improvement": total_improvement,
            "additional_approvals_monthly": int(additional_approvals_monthly),
            "additional_revenue_monthly": round(additional_revenue_monthly, 2),
            "annual_revenue_impact": round(annual_revenue, 2),
            "implementation_cost": implementation_cost,
            "annual_operational_cost": annual_operational_cost,
            "first_year_roi_percent": round(first_year_roi, 1),
            "payback_period_months": round(payback_months, 1),
            "recommendation": "HIGHLY RECOMMENDED" if first_year_roi > 200 else "RECOMMENDED"
        }
    
    def _get_action_for_decline_reason(self, decline_reason_code: str) -> str:
        """Get recommended action for a decline reason"""
        actions = {
            "51": "Implement Smart Retry with 24-72 hour delay for optimal recovery",
            "05": "Engage with issuer for policy clarification; consider smart routing",
            "12": "Review transaction data quality and formatting",
            "41": "Do not retry; card reported lost",
            "43": "Do not retry; card reported stolen",
            "54": "Implement Account Updater service to refresh card details",
            "55": "Prompt customer to verify PIN",
            "57": "Route through alternative acquirer or payment method",
            "59": "Review fraud detection thresholds; may be false positive",
            "61": "Offer split payment or alternative payment method",
            "62": "Contact issuer for restriction details",
            "63": "Review security protocols and authentication methods",
            "65": "Retry after limit reset period (typically 24 hours)"
        }
        return actions.get(decline_reason_code, "Analyze pattern and consult with issuer")
    
    def chat(self, message: str, conversation_history: list = None) -> dict:
        """
        Chat with the agent using natural language
        
        Args:
            message: User message
            conversation_history: Previous conversation messages
            
        Returns:
            Agent response with recommendations
        """
        if conversation_history is None:
            conversation_history = []
        
        # Add system prompt if this is the first message
        if not conversation_history:
            conversation_history.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # Add user message
        conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Process the message and generate response
        # In production, this would call the Databricks Model Serving endpoint
        # For demo, we'll use rule-based responses
        
        response = self._generate_response(message)
        
        conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return {
            "response": response,
            "conversation_history": conversation_history
        }
    
    def _generate_response(self, message: str) -> str:
        """Generate response based on message content"""
        message_lower = message.lower()
        
        if "approval rate" in message_lower or "how are we doing" in message_lower:
            metrics = self.get_approval_metrics()
            return f"""Based on the last 7 days, here are your key metrics:

📊 **Overall Performance:**
- Total Transactions: {metrics['total_transactions']:,}
- Approval Rate: {metrics['approval_rate']:.1%}
- Trend: {metrics['trend']}

🎯 **Top Performing Solution:** {metrics['top_performing_solution']}

💡 **Opportunity:** {metrics['improvement_opportunity']}

Would you like me to analyze specific decline reasons or recommend optimization strategies?"""
        
        elif "decline" in message_lower or "why" in message_lower:
            analysis = self.analyze_decline_reasons()
            return f"""Here's an analysis of your decline patterns:

📉 **Decline Overview:**
- Total Declines: {analysis['total_declines']:,}
- Decline Rate: {analysis['decline_rate']:.1%}
- Recoverable: {analysis['recoverable_percentage']:.1%}

🔝 **Top Decline Reasons:**
1. {analysis['top_reasons'][0]['description']} ({analysis['top_reasons'][0]['count']:,} transactions)
2. {analysis['top_reasons'][1]['description']} ({analysis['top_reasons'][1]['count']:,} transactions)
3. {analysis['top_reasons'][2]['description']} ({analysis['top_reasons'][2]['count']:,} transactions)

💰 **Estimated Recovery Value:** ${analysis['estimated_recovery_value']:,}

Would you like specific recommendations for any of these decline reasons?"""
        
        elif "retry" in message_lower:
            return """I can help you optimize your retry strategy! 

🔄 **Smart Retry Benefits:**
- 30-40% recovery rate on insufficient funds declines
- Optimal timing based on decline reason
- Prevents low-probability retries to reduce costs

**Key Recommendations:**
1. **Insufficient Funds (Code 51):** Retry after 24-72 hours (65% success rate)
2. **Limit Exceeded (Codes 61, 65):** Retry after 24 hours (55% success rate)
3. **Fraud-Related (Codes 41, 43, 59):** Do not retry

Would you like me to analyze a specific declined transaction for retry recommendation?"""
        
        elif "roi" in message_lower or "cost" in message_lower or "value" in message_lower:
            roi = self.calculate_roi(1000000, 100, 0.85)
            return f"""Here's the ROI analysis for implementing approval optimization:

💰 **Financial Impact:**
- Current Approval Rate: {roi['current_approval_rate']:.1%}
- Projected Approval Rate: {roi['projected_approval_rate']:.1%}
- Additional Monthly Revenue: ${roi['additional_revenue_monthly']:,.0f}
- Annual Revenue Impact: ${roi['annual_revenue_impact']:,.0f}

📊 **Investment:**
- Implementation Cost: ${roi['implementation_cost']:,}
- Annual Operational Cost: ${roi['annual_operational_cost']:,}
- First Year ROI: {roi['first_year_roi_percent']:.0f}%
- Payback Period: {roi['payback_period_months']:.1f} months

✅ **Recommendation:** {roi['recommendation']}

This represents a strong business case for implementation!"""
        
        else:
            return """I'm your AI assistant for payment approval optimization! I can help you with:

🎯 **Smart Checkout:** Recommend optimal payment solutions for transactions
📉 **Decline Analysis:** Identify patterns and root causes
🔄 **Smart Retry:** Optimize retry timing and conditions
💰 **ROI Calculation:** Estimate business impact

What would you like to know more about?"""


def main():
    """Demo the agent"""
    agent = ApprovalOptimizerAgent()
    
    print("=== Approval Optimizer Agent Demo ===\n")
    
    # Example conversations
    conversations = [
        "How are we doing with approval rates?",
        "What are the main reasons for declines?",
        "Should I retry a transaction that was declined for insufficient funds 30 hours ago?",
        "What's the ROI if we implement these optimizations?"
    ]
    
    conversation_history = []
    
    for user_message in conversations:
        print(f"User: {user_message}")
        result = agent.chat(user_message, conversation_history)
        print(f"\nAgent: {result['response']}\n")
        print("-" * 80 + "\n")
        conversation_history = result['conversation_history']


if __name__ == "__main__":
    main()
