"""
Cardholder Data Generator for Payment Approval Demo

Generates synthetic cardholder profiles with risk indicators
and behavioral patterns.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from faker import Faker
import numpy as np


class CardholderGenerator:
    """Generate synthetic cardholder profiles"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the cardholder generator
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        np.random.seed(seed)
        self.faker = Faker()
        Faker.seed(seed)
        
        self.geographies = ["US", "UK", "EU", "LATAM", "APAC"]
        self.geography_weights = [0.35, 0.15, 0.20, 0.15, 0.15]
        
        self.risk_segments = ["LOW", "MEDIUM", "HIGH", "VIP"]
        self.risk_segment_weights = [0.60, 0.25, 0.10, 0.05]
        
        self.card_types = ["CREDIT", "DEBIT", "PREPAID"]
        self.card_type_weights = [0.60, 0.35, 0.05]
        
    def generate_cardholder(self, cardholder_id: str = None) -> Dict[str, Any]:
        """
        Generate a single cardholder profile
        
        Args:
            cardholder_id: Optional cardholder ID (generated if not provided)
            
        Returns:
            Dictionary containing cardholder data
        """
        if cardholder_id is None:
            cardholder_id = f"CH{str(uuid.uuid4().int)[:10]}"
            
        geography = random.choices(self.geographies, weights=self.geography_weights)[0]
        country = self._get_country_from_geography(geography)
        
        # Generate cardholder details
        gender = random.choice(["M", "F", "O"])
        if gender == "M":
            first_name = self.faker.first_name_male()
        elif gender == "F":
            first_name = self.faker.first_name_female()
        else:
            first_name = self.faker.first_name()
            
        last_name = self.faker.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@{self.faker.free_email_domain()}"
        
        # Age distribution (18-80)
        age = int(np.random.gamma(shape=3, scale=10) + 18)
        age = min(80, max(18, age))
        
        # Account age in months (1-120)
        account_age_months = int(np.random.gamma(shape=2, scale=15))
        account_age_months = min(120, max(1, account_age_months))
        
        # Card details
        card_type = random.choices(self.card_types, weights=self.card_type_weights)[0]
        risk_segment = random.choices(self.risk_segments, weights=self.risk_segment_weights)[0]
        
        # Risk indicators
        if risk_segment == "LOW":
            risk_score = round(np.random.beta(2, 8) * 100, 2)  # Low scores
            credit_limit = round(np.random.lognormal(mean=8.5, sigma=0.5), 2)
        elif risk_segment == "MEDIUM":
            risk_score = round(np.random.beta(4, 6) * 100, 2)  # Medium scores
            credit_limit = round(np.random.lognormal(mean=8.0, sigma=0.5), 2)
        elif risk_segment == "HIGH":
            risk_score = round(np.random.beta(7, 3) * 100, 2)  # High scores
            credit_limit = round(np.random.lognormal(mean=7.5, sigma=0.5), 2)
        else:  # VIP
            risk_score = round(np.random.beta(1, 10) * 100, 2)  # Very low scores
            credit_limit = round(np.random.lognormal(mean=10.0, sigma=0.5), 2)
            
        # Behavioral patterns
        avg_monthly_transactions = int(np.random.gamma(shape=3, scale=5))
        avg_monthly_transactions = max(1, avg_monthly_transactions)
        
        avg_transaction_amount = round(np.random.lognormal(mean=4.0, sigma=1.0), 2)
        
        # Historical performance
        historical_approval_rate = round(np.random.beta(20, 3), 4)  # Most cardholders have high approval rates
        historical_decline_count = int(np.random.poisson(lam=2))
        historical_fraud_incidents = int(np.random.poisson(lam=0.1))  # Rare
        
        # 3DS enrollment
        threeds_enrolled = random.random() < 0.70
        
        # Digital wallet enrollment
        digital_wallet_enrolled = random.random() < 0.45
        wallet_types = []
        if digital_wallet_enrolled:
            available_wallets = ["ApplePay", "GooglePay", "PayPal", "SamsungPay"]
            num_wallets = random.randint(1, 3)
            wallet_types = random.sample(available_wallets, num_wallets)
            
        # Biometric authentication
        biometric_enabled = random.random() < 0.55
        
        # Card dates
        account_created = datetime.now() - timedelta(days=account_age_months * 30)
        card_expiry = datetime.now() + timedelta(days=random.randint(180, 1825))  # 6 months to 5 years
        
        cardholder = {
            "cardholder_id": cardholder_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "gender": gender,
            "age": age,
            "geography": geography,
            "country": country,
            "city": self.faker.city(),
            "postal_code": self.faker.postcode(),
            "card_type": card_type,
            "risk_segment": risk_segment,
            "risk_score": risk_score,
            "credit_limit": credit_limit,
            "account_age_months": account_age_months,
            "account_created": account_created.isoformat(),
            "card_expiry": card_expiry.isoformat(),
            "avg_monthly_transactions": avg_monthly_transactions,
            "avg_transaction_amount": avg_transaction_amount,
            "historical_approval_rate": historical_approval_rate,
            "historical_decline_count": historical_decline_count,
            "historical_fraud_incidents": historical_fraud_incidents,
            "threeds_enrolled": threeds_enrolled,
            "digital_wallet_enrolled": digital_wallet_enrolled,
            "wallet_types": ",".join(wallet_types) if wallet_types else None,
            "biometric_enabled": biometric_enabled,
            "is_active": True,
            "last_transaction_date": None,
            "kyc_verified": random.random() < 0.95,
            "email_verified": random.random() < 0.90,
            "phone_verified": random.random() < 0.85,
            "address_verified": random.random() < 0.80,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return cardholder
    
    def generate_batch(self, num_cardholders: int) -> pd.DataFrame:
        """
        Generate a batch of cardholders
        
        Args:
            num_cardholders: Number of cardholders to generate
            
        Returns:
            DataFrame containing generated cardholders
        """
        cardholders = []
        
        for i in range(num_cardholders):
            cardholder_id = f"CH{str(i + 1).zfill(10)}"
            cardholder = self.generate_cardholder(cardholder_id)
            cardholders.append(cardholder)
            
        return pd.DataFrame(cardholders)
    
    def update_cardholder_stats(
        self,
        cardholder: Dict[str, Any],
        transaction_approved: bool,
        transaction_amount: float,
        transaction_date: datetime
    ) -> Dict[str, Any]:
        """
        Update cardholder statistics based on transaction
        
        Args:
            cardholder: Cardholder dictionary
            transaction_approved: Whether transaction was approved
            transaction_amount: Transaction amount
            transaction_date: Transaction date
            
        Returns:
            Updated cardholder dictionary
        """
        updated_cardholder = cardholder.copy()
        
        # Update last transaction date
        updated_cardholder["last_transaction_date"] = transaction_date.isoformat()
        
        # Update approval rate (exponential moving average)
        alpha = 0.1  # Smoothing factor
        current_rate = updated_cardholder["historical_approval_rate"]
        new_value = 1.0 if transaction_approved else 0.0
        updated_cardholder["historical_approval_rate"] = round(
            alpha * new_value + (1 - alpha) * current_rate, 4
        )
        
        # Update decline count
        if not transaction_approved:
            updated_cardholder["historical_decline_count"] += 1
            
        # Update average transaction amount (exponential moving average)
        current_avg = updated_cardholder["avg_transaction_amount"]
        updated_cardholder["avg_transaction_amount"] = round(
            alpha * transaction_amount + (1 - alpha) * current_avg, 2
        )
        
        updated_cardholder["updated_at"] = datetime.now().isoformat()
        
        return updated_cardholder
    
    def _get_country_from_geography(self, geography: str) -> str:
        """Map geography to a specific country"""
        country_mapping = {
            "US": ["US"],
            "UK": ["GB"],
            "EU": ["DE", "FR", "ES", "IT", "NL", "SE", "PL", "BE"],
            "LATAM": ["BR", "MX", "AR", "CL", "CO", "PE"],
            "APAC": ["JP", "AU", "SG", "KR", "IN", "CN", "ID"]
        }
        return random.choice(country_mapping[geography])


def main():
    """Demo usage of the cardholder generator"""
    generator = CardholderGenerator()
    
    # Generate batch of cardholders
    print("Generating 10,000 cardholders...")
    cardholders_df = generator.generate_batch(num_cardholders=10000)
    
    print(f"\nGenerated {len(cardholders_df)} cardholders")
    print(f"\nRisk Segment Distribution:")
    print(cardholders_df['risk_segment'].value_counts())
    
    print(f"\nGeography Distribution:")
    print(cardholders_df['geography'].value_counts())
    
    print(f"\nCard Type Distribution:")
    print(cardholders_df['card_type'].value_counts())
    
    print(f"\n3DS Enrollment Rate: {cardholders_df['threeds_enrolled'].mean():.2%}")
    print(f"Digital Wallet Enrollment Rate: {cardholders_df['digital_wallet_enrolled'].mean():.2%}")
    print(f"Biometric Enabled Rate: {cardholders_df['biometric_enabled'].mean():.2%}")
    
    print(f"\nSample cardholders:")
    print(cardholders_df.head())
    
    # Save to CSV
    output_file = "sample_cardholders.csv"
    cardholders_df.to_csv(output_file, index=False)
    print(f"\nCardholders saved to {output_file}")


if __name__ == "__main__":
    main()
