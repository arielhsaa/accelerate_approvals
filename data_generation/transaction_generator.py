"""
Transaction Data Generator for Payment Approval Demo

Generates synthetic credit card transaction data with realistic patterns
for demonstrating approval rate optimization.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from faker import Faker
import numpy as np


class TransactionGenerator:
    """Generate synthetic payment transactions"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the transaction generator
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        np.random.seed(seed)
        self.faker = Faker()
        Faker.seed(seed)
        
        # Transaction patterns
        self.card_networks = ["VISA", "MASTERCARD", "AMEX", "DISCOVER"]
        self.card_network_weights = [0.50, 0.35, 0.10, 0.05]
        
        self.transaction_types = ["PURCHASE", "RECURRING", "REFUND", "AUTHORIZATION"]
        self.transaction_type_weights = [0.70, 0.20, 0.05, 0.05]
        
        self.currencies = ["USD", "EUR", "GBP", "BRL", "MXN", "JPY", "AUD"]
        self.currency_weights = [0.40, 0.20, 0.10, 0.10, 0.10, 0.05, 0.05]
        
        self.geographies = ["US", "UK", "EU", "LATAM", "APAC"]
        self.geography_weights = [0.35, 0.15, 0.20, 0.15, 0.15]
        
        # Decline reasons
        self.decline_reasons = {
            "51": "Insufficient Funds",
            "05": "Do Not Honor",
            "12": "Invalid Transaction",
            "41": "Lost Card",
            "43": "Stolen Card",
            "54": "Expired Card",
            "55": "Incorrect PIN",
            "57": "Transaction Not Permitted",
            "59": "Suspected Fraud",
            "61": "Exceeds Withdrawal Limit",
            "62": "Restricted Card",
            "63": "Security Violation",
            "65": "Exceeds Frequency Limit"
        }
        
        self.decline_reason_weights = [0.35, 0.20, 0.10, 0.05, 0.05, 0.08, 0.03, 0.05, 0.04, 0.02, 0.01, 0.01, 0.01]
        
    def generate_transaction(
        self,
        cardholder_id: str,
        merchant_id: str,
        timestamp: datetime = None
    ) -> Dict[str, Any]:
        """
        Generate a single transaction
        
        Args:
            cardholder_id: Unique cardholder identifier
            merchant_id: Unique merchant identifier
            timestamp: Transaction timestamp (defaults to now)
            
        Returns:
            Dictionary containing transaction data
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # Generate basic transaction details
        transaction_id = str(uuid.uuid4())
        card_network = random.choices(self.card_networks, weights=self.card_network_weights)[0]
        transaction_type = random.choices(self.transaction_types, weights=self.transaction_type_weights)[0]
        currency = random.choices(self.currencies, weights=self.currency_weights)[0]
        geography = random.choices(self.geographies, weights=self.geography_weights)[0]
        
        # Generate transaction amount (log-normal distribution for realistic amounts)
        base_amount = np.random.lognormal(mean=3.5, sigma=1.2)
        amount = round(max(1.0, min(10000.0, base_amount)), 2)
        
        # Determine approval based on multiple factors
        base_approval_rate = 0.85
        
        # Adjust approval rate based on factors
        amount_factor = -0.05 if amount > 1000 else 0.0
        geography_factor = {"US": 0.05, "UK": 0.03, "EU": 0.02, "LATAM": -0.03, "APAC": 0.0}[geography]
        transaction_type_factor = {"PURCHASE": 0.0, "RECURRING": 0.05, "REFUND": 0.10, "AUTHORIZATION": 0.02}[transaction_type]
        
        # Time-based factors (lower approval at night)
        hour = timestamp.hour
        time_factor = -0.05 if (hour < 6 or hour > 22) else 0.0
        
        # Day of week factor (lower on weekends for some merchants)
        day_of_week = timestamp.weekday()
        dow_factor = -0.02 if day_of_week >= 5 else 0.0
        
        # Calculate final approval probability
        approval_probability = base_approval_rate + amount_factor + geography_factor + transaction_type_factor + time_factor + dow_factor
        approval_probability = max(0.0, min(1.0, approval_probability))
        
        is_approved = random.random() < approval_probability
        
        # Generate decline reason if declined
        decline_reason_code = None
        decline_reason_description = None
        if not is_approved:
            decline_reason_code = random.choices(
                list(self.decline_reasons.keys()),
                weights=self.decline_reason_weights
            )[0]
            decline_reason_description = self.decline_reasons[decline_reason_code]
        
        # Generate fraud score (0-100)
        fraud_score = round(np.random.beta(2, 20) * 100, 2)  # Most transactions have low fraud scores
        
        # Generate 3DS flags
        requires_3ds = amount > 500 or fraud_score > 50 or random.random() < 0.3
        threeds_authenticated = requires_3ds and random.random() < 0.85
        
        # Payment solution applied (simulate smart routing)
        payment_solutions_applied = []
        if requires_3ds:
            payment_solutions_applied.append("3DS")
        if fraud_score > 40:
            payment_solutions_applied.append("Antifraud")
        if amount > 1000:
            payment_solutions_applied.append("IDPay")
        if random.random() < 0.2:
            payment_solutions_applied.append("NetworkToken")
        if random.random() < 0.1:
            payment_solutions_applied.append("Passkey")
        if len(payment_solutions_applied) == 0:
            payment_solutions_applied.append("DataShareOnly")
            
        # Processing metrics
        processing_time_ms = round(np.random.gamma(shape=2, scale=50), 2)  # Gamma distribution for latency
        
        transaction = {
            "transaction_id": transaction_id,
            "cardholder_id": cardholder_id,
            "merchant_id": merchant_id,
            "timestamp": timestamp.isoformat(),
            "amount": amount,
            "currency": currency,
            "card_network": card_network,
            "transaction_type": transaction_type,
            "geography": geography,
            "merchant_country": self._get_country_from_geography(geography),
            "cardholder_country": self._get_country_from_geography(geography),
            "is_approved": is_approved,
            "decline_reason_code": decline_reason_code,
            "decline_reason_description": decline_reason_description,
            "fraud_score": fraud_score,
            "requires_3ds": requires_3ds,
            "threeds_authenticated": threeds_authenticated,
            "payment_solutions_applied": ",".join(payment_solutions_applied),
            "processing_time_ms": processing_time_ms,
            "hour_of_day": hour,
            "day_of_week": day_of_week,
            "day_of_month": timestamp.day,
            "is_weekend": day_of_week >= 5,
            "is_cross_border": random.random() < 0.15,
            "is_card_present": random.random() < 0.30,
            "merchant_initiated": transaction_type == "RECURRING",
            "retry_attempt": 0,
            "original_transaction_id": None
        }
        
        return transaction
    
    def generate_batch(
        self,
        num_transactions: int,
        cardholder_ids: List[str],
        merchant_ids: List[str],
        start_time: datetime = None,
        time_range_hours: int = 24
    ) -> pd.DataFrame:
        """
        Generate a batch of transactions
        
        Args:
            num_transactions: Number of transactions to generate
            cardholder_ids: List of cardholder IDs to sample from
            merchant_ids: List of merchant IDs to sample from
            start_time: Start time for transactions
            time_range_hours: Time range for transaction distribution
            
        Returns:
            DataFrame containing generated transactions
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=time_range_hours)
            
        transactions = []
        
        for _ in range(num_transactions):
            # Random cardholder and merchant
            cardholder_id = random.choice(cardholder_ids)
            merchant_id = random.choice(merchant_ids)
            
            # Random timestamp within range
            random_offset = timedelta(seconds=random.randint(0, time_range_hours * 3600))
            timestamp = start_time + random_offset
            
            transaction = self.generate_transaction(cardholder_id, merchant_id, timestamp)
            transactions.append(transaction)
            
        df = pd.DataFrame(transactions)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def generate_streaming_batch(
        self,
        cardholder_ids: List[str],
        merchant_ids: List[str],
        batch_size: int = 100
    ) -> pd.DataFrame:
        """
        Generate a batch for streaming simulation (current timestamp)
        
        Args:
            cardholder_ids: List of cardholder IDs
            merchant_ids: List of merchant IDs
            batch_size: Number of transactions in batch
            
        Returns:
            DataFrame containing transactions
        """
        transactions = []
        base_time = datetime.now()
        
        for i in range(batch_size):
            cardholder_id = random.choice(cardholder_ids)
            merchant_id = random.choice(merchant_ids)
            
            # Spread transactions across 1 second
            timestamp = base_time + timedelta(milliseconds=i * 10)
            
            transaction = self.generate_transaction(cardholder_id, merchant_id, timestamp)
            transactions.append(transaction)
            
        return pd.DataFrame(transactions)
    
    def generate_retry_transaction(
        self,
        original_transaction: Dict[str, Any],
        retry_delay_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate a retry transaction based on an original declined transaction
        
        Args:
            original_transaction: The original declined transaction
            retry_delay_hours: Hours since original transaction
            
        Returns:
            Retry transaction dictionary
        """
        original_timestamp = datetime.fromisoformat(original_transaction["timestamp"])
        retry_timestamp = original_timestamp + timedelta(hours=retry_delay_hours)
        
        retry_transaction = original_transaction.copy()
        retry_transaction["transaction_id"] = str(uuid.uuid4())
        retry_transaction["timestamp"] = retry_timestamp.isoformat()
        retry_transaction["retry_attempt"] = original_transaction.get("retry_attempt", 0) + 1
        retry_transaction["original_transaction_id"] = original_transaction["transaction_id"]
        
        # Retry has different approval probability based on decline reason
        decline_code = original_transaction["decline_reason_code"]
        
        # Higher success rate for insufficient funds after delay
        if decline_code == "51" and retry_delay_hours >= 24:
            retry_success_rate = 0.65
        # Lower success rate for fraud-related declines
        elif decline_code in ["41", "43", "59", "63"]:
            retry_success_rate = 0.05
        # Expired card won't succeed unless card is replaced
        elif decline_code == "54":
            retry_success_rate = 0.10
        # Other reasons have moderate retry success
        else:
            retry_success_rate = 0.35
            
        is_approved = random.random() < retry_success_rate
        
        retry_transaction["is_approved"] = is_approved
        if is_approved:
            retry_transaction["decline_reason_code"] = None
            retry_transaction["decline_reason_description"] = None
        
        return retry_transaction
    
    def _get_country_from_geography(self, geography: str) -> str:
        """Map geography to a specific country"""
        country_mapping = {
            "US": ["US"],
            "UK": ["GB"],
            "EU": ["DE", "FR", "ES", "IT", "NL", "SE"],
            "LATAM": ["BR", "MX", "AR", "CL", "CO"],
            "APAC": ["JP", "AU", "SG", "KR", "IN"]
        }
        return random.choice(country_mapping[geography])


def main():
    """Demo usage of the transaction generator"""
    generator = TransactionGenerator()
    
    # Generate sample cardholder and merchant IDs
    cardholder_ids = [f"CH{str(i).zfill(6)}" for i in range(1, 101)]
    merchant_ids = [f"MER{str(i).zfill(5)}" for i in range(1, 51)]
    
    # Generate batch of transactions
    print("Generating 1000 transactions...")
    transactions_df = generator.generate_batch(
        num_transactions=1000,
        cardholder_ids=cardholder_ids,
        merchant_ids=merchant_ids,
        time_range_hours=168  # 1 week
    )
    
    print(f"\nGenerated {len(transactions_df)} transactions")
    print(f"Approval Rate: {transactions_df['is_approved'].mean():.2%}")
    print(f"\nSample transactions:")
    print(transactions_df.head())
    
    # Show decline reason distribution
    print("\nDecline Reason Distribution:")
    decline_df = transactions_df[~transactions_df['is_approved']]
    print(decline_df['decline_reason_description'].value_counts())
    
    # Save to CSV
    output_file = "sample_transactions.csv"
    transactions_df.to_csv(output_file, index=False)
    print(f"\nTransactions saved to {output_file}")


if __name__ == "__main__":
    main()
