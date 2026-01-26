"""
Merchant Data Generator for Payment Approval Demo

Generates synthetic merchant profiles with risk scores and
category classifications.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from faker import Faker
import numpy as np


class MerchantGenerator:
    """Generate synthetic merchant profiles"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the merchant generator
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        np.random.seed(seed)
        self.faker = Faker()
        Faker.seed(seed)
        
        # Merchant Category Codes (MCC)
        self.merchant_categories = {
            "5411": "Grocery Stores",
            "5812": "Restaurants",
            "5541": "Service Stations",
            "5912": "Drug Stores",
            "5331": "Variety Stores",
            "5722": "Household Appliance Stores",
            "5311": "Department Stores",
            "5999": "Miscellaneous Retail",
            "7011": "Hotels/Motels",
            "4121": "Taxicabs/Limousines",
            "5814": "Fast Food Restaurants",
            "5942": "Book Stores",
            "5732": "Electronics Stores",
            "7832": "Motion Picture Theaters",
            "5661": "Shoe Stores",
            "5691": "Clothing Stores",
            "5511": "Car Dealers",
            "5912": "Pharmacies",
            "5310": "Discount Stores",
            "7230": "Beauty/Barber Shops",
            "5812": "Eating Places",
            "5947": "Gift/Novelty Shops",
            "5621": "Women's Clothing",
            "5065": "Electronics Parts",
            "7994": "Video Game Arcades",
            "5815": "Digital Goods - Media",
            "5816": "Digital Goods - Games",
            "5817": "Digital Goods - Applications",
            "5818": "Digital Goods - Large",
            "6211": "Securities Brokers",
            "6300": "Insurance Sales",
            "7995": "Gambling/Casino",
            "5993": "Tobacco Stores"
        }
        
        self.mcc_weights = [
            0.12, 0.10, 0.08, 0.06, 0.05, 0.04, 0.06, 0.05,
            0.04, 0.02, 0.08, 0.02, 0.05, 0.02, 0.02, 0.03,
            0.02, 0.02, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01,
            0.01, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01
        ]
        
        self.geographies = ["US", "UK", "EU", "LATAM", "APAC"]
        self.geography_weights = [0.35, 0.15, 0.20, 0.15, 0.15]
        
        self.merchant_size = ["SMALL", "MEDIUM", "LARGE", "ENTERPRISE"]
        self.size_weights = [0.50, 0.30, 0.15, 0.05]
        
    def generate_merchant(self, merchant_id: str = None) -> Dict[str, Any]:
        """
        Generate a single merchant profile
        
        Args:
            merchant_id: Optional merchant ID (generated if not provided)
            
        Returns:
            Dictionary containing merchant data
        """
        if merchant_id is None:
            merchant_id = f"MER{str(uuid.uuid4().int)[:10]}"
            
        # Select MCC and category
        mcc = random.choices(list(self.merchant_categories.keys()), weights=self.mcc_weights)[0]
        category = self.merchant_categories[mcc]
        
        # Geography and location
        geography = random.choices(self.geographies, weights=self.geography_weights)[0]
        country = self._get_country_from_geography(geography)
        
        # Merchant details
        merchant_size = random.choices(self.merchant_size, weights=self.size_weights)[0]
        
        # Generate merchant name based on category
        merchant_name = self._generate_merchant_name(category)
        
        # Business age in months (1-240, with bias towards established businesses)
        business_age_months = int(np.random.gamma(shape=3, scale=20))
        business_age_months = min(240, max(1, business_age_months))
        
        # Risk scoring based on multiple factors
        base_risk_score = 50
        
        # High-risk categories
        high_risk_mccs = ["7995", "5993", "6211", "5816", "5817", "5818"]
        if mcc in high_risk_mccs:
            base_risk_score += random.randint(20, 40)
        
        # Age factor (newer businesses are riskier)
        if business_age_months < 12:
            base_risk_score += random.randint(10, 20)
        elif business_age_months > 60:
            base_risk_score -= random.randint(5, 15)
            
        # Size factor (larger merchants are typically lower risk)
        if merchant_size == "ENTERPRISE":
            base_risk_score -= random.randint(10, 20)
        elif merchant_size == "SMALL":
            base_risk_score += random.randint(5, 15)
            
        # Add some randomness
        risk_score = base_risk_score + random.randint(-10, 10)
        risk_score = max(0, min(100, risk_score))
        
        # Approval rate (inversely related to risk)
        base_approval_rate = 0.90 - (risk_score / 200)
        approval_rate = round(max(0.50, min(0.99, base_approval_rate)), 4)
        
        # Volume metrics based on size
        if merchant_size == "SMALL":
            avg_daily_transactions = int(np.random.gamma(shape=2, scale=50))
            avg_monthly_volume = round(np.random.lognormal(mean=9.0, sigma=1.0), 2)
        elif merchant_size == "MEDIUM":
            avg_daily_transactions = int(np.random.gamma(shape=3, scale=150))
            avg_monthly_volume = round(np.random.lognormal(mean=11.0, sigma=1.0), 2)
        elif merchant_size == "LARGE":
            avg_daily_transactions = int(np.random.gamma(shape=4, scale=500))
            avg_monthly_volume = round(np.random.lognormal(mean=13.0, sigma=1.0), 2)
        else:  # ENTERPRISE
            avg_daily_transactions = int(np.random.gamma(shape=5, scale=2000))
            avg_monthly_volume = round(np.random.lognormal(mean=15.0, sigma=1.0), 2)
            
        # Average ticket size
        avg_ticket_size = round(np.random.lognormal(mean=4.0, sigma=1.0), 2)
        
        # Chargeback metrics
        chargeback_rate = round(np.random.beta(2, 98), 4)  # Most merchants have low chargeback rates
        fraud_rate = round(np.random.beta(1, 199), 4)  # Most merchants have very low fraud rates
        
        # Integration and capabilities
        threeds_enabled = random.random() < 0.75
        network_token_enabled = random.random() < 0.60
        recurring_billing_enabled = random.random() < 0.40
        
        # Supported payment methods
        supports_credit = True
        supports_debit = random.random() < 0.95
        supports_digital_wallets = random.random() < 0.70
        supports_bnpl = random.random() < 0.30  # Buy Now Pay Later
        
        # Compliance and verification
        pci_compliant = random.random() < 0.95
        kyb_verified = random.random() < 0.90  # Know Your Business
        
        # Settlement details
        settlement_currency = self._get_currency_from_geography(geography)
        settlement_period_days = random.choice([1, 2, 3, 7])
        
        # Dates
        onboarded_date = datetime.now() - timedelta(days=business_age_months * 30)
        
        merchant = {
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "mcc": mcc,
            "category": category,
            "merchant_size": merchant_size,
            "geography": geography,
            "country": country,
            "city": self.faker.city(),
            "postal_code": self.faker.postcode(),
            "business_age_months": business_age_months,
            "onboarded_date": onboarded_date.isoformat(),
            "risk_score": risk_score,
            "approval_rate": approval_rate,
            "avg_daily_transactions": avg_daily_transactions,
            "avg_monthly_volume": avg_monthly_volume,
            "avg_ticket_size": avg_ticket_size,
            "chargeback_rate": chargeback_rate,
            "fraud_rate": fraud_rate,
            "threeds_enabled": threeds_enabled,
            "network_token_enabled": network_token_enabled,
            "recurring_billing_enabled": recurring_billing_enabled,
            "supports_credit": supports_credit,
            "supports_debit": supports_debit,
            "supports_digital_wallets": supports_digital_wallets,
            "supports_bnpl": supports_bnpl,
            "pci_compliant": pci_compliant,
            "kyb_verified": kyb_verified,
            "settlement_currency": settlement_currency,
            "settlement_period_days": settlement_period_days,
            "is_active": True,
            "last_transaction_date": None,
            "total_lifetime_volume": 0.0,
            "total_lifetime_transactions": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return merchant
    
    def generate_batch(self, num_merchants: int) -> pd.DataFrame:
        """
        Generate a batch of merchants
        
        Args:
            num_merchants: Number of merchants to generate
            
        Returns:
            DataFrame containing generated merchants
        """
        merchants = []
        
        for i in range(num_merchants):
            merchant_id = f"MER{str(i + 1).zfill(8)}"
            merchant = self.generate_merchant(merchant_id)
            merchants.append(merchant)
            
        return pd.DataFrame(merchants)
    
    def _generate_merchant_name(self, category: str) -> str:
        """Generate a realistic merchant name based on category"""
        prefixes = ["The", "Super", "Best", "Top", "Premium", "Quality", "Fresh", "Quick", "Express", "Smart"]
        suffixes = ["Shop", "Store", "Market", "Plus", "World", "Center", "Outlet", "Direct", "Online", "Express"]
        
        # Category-specific names
        if "Restaurant" in category or "Food" in category or "Eating" in category:
            types = ["Bistro", "Cafe", "Grill", "Kitchen", "Diner", "Eatery", "Restaurant"]
            return f"{self.faker.last_name()}'s {random.choice(types)}"
        elif "Hotel" in category:
            types = ["Hotel", "Inn", "Resort", "Suites", "Lodge"]
            return f"{random.choice(prefixes)} {self.faker.city()} {random.choice(types)}"
        elif "Store" in category or "Shop" in category:
            return f"{random.choice(prefixes)} {random.choice(suffixes)}"
        elif "Digital" in category:
            tech_words = ["Cloud", "Byte", "Pixel", "Data", "Net", "Cyber", "Tech", "Digital"]
            return f"{random.choice(tech_words)}{random.choice(suffixes)}"
        else:
            return f"{self.faker.company()}"
    
    def _get_country_from_geography(self, geography: str) -> str:
        """Map geography to a specific country"""
        country_mapping = {
            "US": ["US"],
            "UK": ["GB"],
            "EU": ["DE", "FR", "ES", "IT", "NL", "SE", "PL", "BE", "AT", "DK"],
            "LATAM": ["BR", "MX", "AR", "CL", "CO", "PE", "VE"],
            "APAC": ["JP", "AU", "SG", "KR", "IN", "CN", "ID", "TH", "MY"]
        }
        return random.choice(country_mapping[geography])
    
    def _get_currency_from_geography(self, geography: str) -> str:
        """Map geography to primary currency"""
        currency_mapping = {
            "US": "USD",
            "UK": "GBP",
            "EU": "EUR",
            "LATAM": random.choice(["BRL", "MXN", "ARS", "CLP"]),
            "APAC": random.choice(["JPY", "AUD", "SGD", "INR"])
        }
        return currency_mapping[geography]


def main():
    """Demo usage of the merchant generator"""
    generator = MerchantGenerator()
    
    # Generate batch of merchants
    print("Generating 5,000 merchants...")
    merchants_df = generator.generate_batch(num_merchants=5000)
    
    print(f"\nGenerated {len(merchants_df)} merchants")
    
    print(f"\nMerchant Size Distribution:")
    print(merchants_df['merchant_size'].value_counts())
    
    print(f"\nGeography Distribution:")
    print(merchants_df['geography'].value_counts())
    
    print(f"\nTop 10 Categories:")
    print(merchants_df['category'].value_counts().head(10))
    
    print(f"\nRisk Score Statistics:")
    print(merchants_df['risk_score'].describe())
    
    print(f"\n3DS Enabled Rate: {merchants_df['threeds_enabled'].mean():.2%}")
    print(f"Network Token Enabled Rate: {merchants_df['network_token_enabled'].mean():.2%}")
    print(f"PCI Compliant Rate: {merchants_df['pci_compliant'].mean():.2%}")
    
    print(f"\nSample merchants:")
    print(merchants_df[['merchant_id', 'merchant_name', 'category', 'merchant_size', 'risk_score']].head(10))
    
    # Save to CSV
    output_file = "sample_merchants.csv"
    merchants_df.to_csv(output_file, index=False)
    print(f"\nMerchants saved to {output_file}")


if __name__ == "__main__":
    main()
