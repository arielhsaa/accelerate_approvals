"""
External Data Generator for Payment Approval Demo

Simulates external data sources for fraud intelligence, 
AML checks, and merchant scoring.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from faker import Faker
import numpy as np


class ExternalDataGenerator:
    """Generate synthetic external data sources"""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the external data generator
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        np.random.seed(seed)
        self.faker = Faker()
        Faker.seed(seed)
        
    def generate_fraud_intelligence(
        self,
        transaction_id: str,
        cardholder_id: str,
        merchant_id: str,
        amount: float,
        geography: str
    ) -> Dict[str, Any]:
        """
        Generate real-time fraud intelligence for a transaction
        
        Args:
            transaction_id: Transaction identifier
            cardholder_id: Cardholder identifier
            merchant_id: Merchant identifier
            amount: Transaction amount
            geography: Geographic region
            
        Returns:
            Dictionary containing fraud intelligence data
        """
        # Base fraud score (most transactions are legitimate)
        base_fraud_score = np.random.beta(2, 18) * 100
        
        # Amount-based risk (higher amounts = higher risk)
        amount_risk = 0
        if amount > 1000:
            amount_risk = 10
        elif amount > 500:
            amount_risk = 5
            
        # Geography risk
        geography_risk = {
            "US": 0,
            "UK": 1,
            "EU": 2,
            "LATAM": 5,
            "APAC": 3
        }.get(geography, 3)
        
        # Calculate final fraud score
        fraud_score = round(min(100, base_fraud_score + amount_risk + geography_risk + random.uniform(-3, 3)), 2)
        
        # Fraud indicators
        velocity_check_1h = random.randint(0, 5)
        velocity_check_24h = random.randint(0, 20)
        
        # Device fingerprint match
        device_fingerprint_match = random.random() < 0.95
        
        # IP geolocation match
        ip_country_match = random.random() < 0.90
        
        # Behavioral anomaly score
        behavioral_anomaly_score = round(np.random.beta(1, 9) * 100, 2)
        
        # Known fraud patterns
        card_testing_pattern = random.random() < 0.02
        account_takeover_pattern = random.random() < 0.01
        synthetic_identity_pattern = random.random() < 0.015
        
        # Risk recommendation
        if fraud_score > 80 or any([card_testing_pattern, account_takeover_pattern, synthetic_identity_pattern]):
            recommendation = "DECLINE"
        elif fraud_score > 60:
            recommendation = "REVIEW"
        elif fraud_score > 40:
            recommendation = "CHALLENGE"  # Request 3DS or additional auth
        else:
            recommendation = "APPROVE"
            
        return {
            "transaction_id": transaction_id,
            "cardholder_id": cardholder_id,
            "merchant_id": merchant_id,
            "fraud_score": fraud_score,
            "recommendation": recommendation,
            "velocity_1h": velocity_check_1h,
            "velocity_24h": velocity_check_24h,
            "device_fingerprint_match": device_fingerprint_match,
            "ip_country_match": ip_country_match,
            "behavioral_anomaly_score": behavioral_anomaly_score,
            "card_testing_pattern": card_testing_pattern,
            "account_takeover_pattern": account_takeover_pattern,
            "synthetic_identity_pattern": synthetic_identity_pattern,
            "timestamp": datetime.now().isoformat(),
            "data_source": "Fraud Intelligence Network"
        }
    
    def generate_aml_screening(
        self,
        entity_id: str,
        entity_type: str,
        entity_name: str,
        country: str
    ) -> Dict[str, Any]:
        """
        Generate AML (Anti-Money Laundering) screening results
        
        Args:
            entity_id: Entity identifier
            entity_type: CARDHOLDER or MERCHANT
            entity_name: Entity name
            country: Country code
            
        Returns:
            Dictionary containing AML screening results
        """
        # AML risk score
        aml_risk_score = round(np.random.beta(2, 18) * 100, 2)
        
        # Watchlist checks
        ofac_match = random.random() < 0.001  # OFAC sanctions list (very rare)
        un_sanctions_match = random.random() < 0.001
        eu_sanctions_match = random.random() < 0.001
        pep_match = random.random() < 0.02  # Politically Exposed Person
        
        # High-risk jurisdiction
        high_risk_countries = ["KP", "IR", "SY", "CU"]  # Example high-risk countries
        high_risk_jurisdiction = country in high_risk_countries
        
        # Transaction pattern indicators
        structuring_indicator = random.random() < 0.01  # Breaking up transactions to avoid reporting
        rapid_movement_indicator = random.random() < 0.02  # Rapid movement of funds
        
        # Overall AML status
        if any([ofac_match, un_sanctions_match, eu_sanctions_match]):
            aml_status = "BLOCKED"
        elif pep_match or high_risk_jurisdiction or aml_risk_score > 80:
            aml_status = "ENHANCED_DUE_DILIGENCE"
        elif aml_risk_score > 50:
            aml_status = "STANDARD_DUE_DILIGENCE"
        else:
            aml_status = "CLEAR"
            
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "country": country,
            "aml_risk_score": aml_risk_score,
            "aml_status": aml_status,
            "ofac_match": ofac_match,
            "un_sanctions_match": un_sanctions_match,
            "eu_sanctions_match": eu_sanctions_match,
            "pep_match": pep_match,
            "high_risk_jurisdiction": high_risk_jurisdiction,
            "structuring_indicator": structuring_indicator,
            "rapid_movement_indicator": rapid_movement_indicator,
            "screening_date": datetime.now().isoformat(),
            "data_source": "AML Screening Service"
        }
    
    def generate_merchant_intelligence(
        self,
        merchant_id: str,
        merchant_name: str,
        mcc: str,
        country: str
    ) -> Dict[str, Any]:
        """
        Generate merchant intelligence and scoring
        
        Args:
            merchant_id: Merchant identifier
            merchant_name: Merchant name
            mcc: Merchant Category Code
            country: Country code
            
        Returns:
            Dictionary containing merchant intelligence
        """
        # Overall merchant score
        merchant_score = round(np.random.beta(8, 2) * 100, 2)  # Most merchants are good
        
        # High-risk MCC categories
        high_risk_mccs = ["7995", "5993", "6211", "5816", "5817", "5818"]
        is_high_risk_category = mcc in high_risk_mccs
        
        # Reputation metrics
        online_reviews_score = round(np.random.beta(5, 2) * 5, 1)  # 0-5 scale
        bbb_rating = random.choice(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "D", "F"])
        
        # Business verification
        business_registered = random.random() < 0.98
        domain_age_days = random.randint(30, 3650)
        ssl_certificate_valid = random.random() < 0.95
        
        # Compliance indicators
        previous_violations = random.random() < 0.05
        data_breach_history = random.random() < 0.02
        
        # Industry reputation
        industry_complaints = int(np.random.poisson(lam=1.5))
        chargebacks_industry_avg = round(random.uniform(0.001, 0.015), 4)
        
        # Trust indicators
        trust_score = round(merchant_score * random.uniform(0.9, 1.1), 2)
        trust_score = min(100, max(0, trust_score))
        
        return {
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "mcc": mcc,
            "country": country,
            "merchant_score": merchant_score,
            "trust_score": trust_score,
            "is_high_risk_category": is_high_risk_category,
            "online_reviews_score": online_reviews_score,
            "bbb_rating": bbb_rating,
            "business_registered": business_registered,
            "domain_age_days": domain_age_days,
            "ssl_certificate_valid": ssl_certificate_valid,
            "previous_violations": previous_violations,
            "data_breach_history": data_breach_history,
            "industry_complaints": industry_complaints,
            "chargebacks_industry_avg": chargebacks_industry_avg,
            "last_updated": datetime.now().isoformat(),
            "data_source": "Merchant Intelligence Platform"
        }
    
    def generate_network_intelligence(
        self,
        card_network: str,
        issuer_country: str
    ) -> Dict[str, Any]:
        """
        Generate card network and issuer intelligence
        
        Args:
            card_network: Card network (VISA, MASTERCARD, etc.)
            issuer_country: Issuer country code
            
        Returns:
            Dictionary containing network intelligence
        """
        # Network-level metrics
        network_fraud_rate = round(random.uniform(0.001, 0.02), 4)
        network_approval_rate = round(random.uniform(0.82, 0.95), 4)
        
        # Issuer performance
        issuer_approval_rate = round(random.uniform(0.80, 0.96), 4)
        issuer_avg_response_time_ms = round(np.random.gamma(shape=2, scale=100), 2)
        
        # Decline reason patterns
        top_decline_reasons = random.sample([
            "Insufficient Funds", "Do Not Honor", "Invalid Transaction",
            "Lost Card", "Suspected Fraud", "Exceeds Withdrawal Limit"
        ], 3)
        
        # Network token support
        network_token_available = card_network in ["VISA", "MASTERCARD"] and random.random() < 0.80
        
        # 3DS support
        threeds_supported = random.random() < 0.90
        threeds_version = "2.0" if random.random() < 0.85 else "1.0"
        
        return {
            "card_network": card_network,
            "issuer_country": issuer_country,
            "network_fraud_rate": network_fraud_rate,
            "network_approval_rate": network_approval_rate,
            "issuer_approval_rate": issuer_approval_rate,
            "issuer_avg_response_time_ms": issuer_avg_response_time_ms,
            "top_decline_reasons": ",".join(top_decline_reasons),
            "network_token_available": network_token_available,
            "threeds_supported": threeds_supported,
            "threeds_version": threeds_version,
            "timestamp": datetime.now().isoformat(),
            "data_source": "Network Intelligence"
        }


def main():
    """Demo usage of the external data generator"""
    generator = ExternalDataGenerator()
    
    # Generate sample data
    print("Generating fraud intelligence...")
    fraud_intel = generator.generate_fraud_intelligence(
        "TXN001", "CH000001", "MER000001", 150.00, "US"
    )
    print(pd.Series(fraud_intel))
    
    print("\n" + "="*50)
    print("Generating AML screening...")
    aml_result = generator.generate_aml_screening(
        "CH000001", "CARDHOLDER", "John Doe", "US"
    )
    print(pd.Series(aml_result))
    
    print("\n" + "="*50)
    print("Generating merchant intelligence...")
    merchant_intel = generator.generate_merchant_intelligence(
        "MER000001", "Test Merchant", "5411", "US"
    )
    print(pd.Series(merchant_intel))
    
    print("\n" + "="*50)
    print("Generating network intelligence...")
    network_intel = generator.generate_network_intelligence("VISA", "US")
    print(pd.Series(network_intel))


if __name__ == "__main__":
    main()
