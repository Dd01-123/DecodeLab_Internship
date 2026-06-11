import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from app.cleaning.config import config


logger = logging.getLogger(__name__)


class BusinessInsightGenerator:
    """
    Enterprise-grade business insight generator.
    
    Automatically analyzes the dataset to extract actionable business
    intelligence across revenue, customer, order, payment, and referral dimensions.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize generator with dataset.
        
        Args:
            df: DataFrame to analyze.
        """
        self.df = df.copy()
        self.insights: Dict[str, Any] = {}
        
    def generate_revenue_insights(self) -> Dict[str, Any]:
        """
        Generate revenue-related business insights.
        
        Returns:
            Dict with revenue insights.
        """
        insights = {'category': 'Revenue Insights'}
        
        if 'TotalPrice' in self.df.columns and 'Product' in self.df.columns:
            # Revenue by product
            product_revenue = self.df.groupby('Product')['TotalPrice'].sum().sort_values(ascending=False)
            
            insights['highest_revenue_product'] = {
                'product': str(product_revenue.index[0]),
                'revenue': round(float(product_revenue.iloc[0]), 2),
            }
            insights['lowest_revenue_product'] = {
                'product': str(product_revenue.index[-1]),
                'revenue': round(float(product_revenue.iloc[-1]), 2),
            }
            
            # Revenue distribution
            insights['total_revenue'] = round(float(self.df['TotalPrice'].sum()), 2)
            insights['average_order_value'] = round(float(self.df['TotalPrice'].mean()), 2)
            insights['median_order_value'] = round(float(self.df['TotalPrice'].median()), 2)
            insights['revenue_std'] = round(float(self.df['TotalPrice'].std()), 2)
            
            # Top 5 products by revenue
            insights['top_5_products'] = {
                str(k): round(float(v), 2) 
                for k, v in product_revenue.head(5).items()
            }
        
        logger.info("Revenue insights generated")
        return insights
    
    def generate_customer_insights(self) -> Dict[str, Any]:
        """
        Generate customer-related business insights.
        
        Returns:
            Dict with customer insights.
        """
        insights = {'category': 'Customer Insights'}
        
        if 'CustomerID' in self.df.columns:
            # Customer activity
            customer_orders = self.df.groupby('CustomerID').size().sort_values(ascending=False)
            
            insights['most_active_customer'] = {
                'customer_id': str(customer_orders.index[0]),
                'order_count': int(customer_orders.iloc[0]),
            }
            
            insights['average_orders_per_customer'] = round(float(customer_orders.mean()), 2)
            insights['median_orders_per_customer'] = round(float(customer_orders.median()), 2)
            insights['total_unique_customers'] = int(self.df['CustomerID'].nunique())
            
            # Customer purchase frequency distribution
            freq_dist = customer_orders.value_counts().sort_index()
            insights['purchase_frequency_distribution'] = {
                str(k): int(v) for k, v in freq_dist.head(10).items()
            }
            
            # Customer lifetime value (if TotalPrice available)
            if 'TotalPrice' in self.df.columns:
                clv = self.df.groupby('CustomerID')['TotalPrice'].sum().sort_values(ascending=False)
                insights['highest_value_customer'] = {
                    'customer_id': str(clv.index[0]),
                    'lifetime_value': round(float(clv.iloc[0]), 2),
                }
                insights['average_customer_lifetime_value'] = round(float(clv.mean()), 2)
        
        logger.info("Customer insights generated")
        return insights
    
    def generate_order_insights(self) -> Dict[str, Any]:
        """
        Generate order-related business insights.
        
        Returns:
            Dict with order insights.
        """
        insights = {'category': 'Order Insights'}
        
        # Order status distribution
        if 'OrderStatus' in self.df.columns:
            status_dist = self.df['OrderStatus'].value_counts()
            insights['order_status_distribution'] = {
                str(k): int(v) for k, v in status_dist.items()
            }
            insights['order_status_percentages'] = {
                str(k): round(float(v) / len(self.df) * 100, 2) 
                for k, v in status_dist.items()
            }
            
            # Fulfillment rate
            fulfilled_statuses = ['Delivered', 'Shipped']
            fulfilled_count = self.df[self.df['OrderStatus'].isin(fulfilled_statuses)].shape[0]
            fulfillment_rate = (fulfilled_count / len(self.df)) * 100 if len(self.df) > 0 else 0
            insights['fulfillment_rate'] = round(float(fulfillment_rate), 2)
            
            # Cancellation rate
            cancelled_count = self.df[self.df['OrderStatus'] == 'Cancelled'].shape[0]
            cancellation_rate = (cancelled_count / len(self.df)) * 100 if len(self.df) > 0 else 0
            insights['cancellation_rate'] = round(float(cancellation_rate), 2)
            
            # Return rate
            returned_count = self.df[self.df['OrderStatus'] == 'Returned'].shape[0]
            return_rate = (returned_count / len(self.df)) * 100 if len(self.df) > 0 else 0
            insights['return_rate'] = round(float(return_rate), 2)
        
        # Quantity insights
        if 'Quantity' in self.df.columns:
            insights['average_quantity_per_order'] = round(float(self.df['Quantity'].mean()), 2)
            insights['most_common_quantity'] = int(self.df['Quantity'].mode().iloc[0]) if len(self.df['Quantity'].mode()) > 0 else None
        
        logger.info("Order insights generated")
        return insights
    
    def generate_payment_insights(self) -> Dict[str, Any]:
        """
        Generate payment-related business insights.
        
        Returns:
            Dict with payment insights.
        """
        insights = {'category': 'Payment Insights'}
        
        if 'PaymentMethod' in self.df.columns:
            payment_dist = self.df['PaymentMethod'].value_counts()
            
            insights['most_used_payment'] = {
                'method': str(payment_dist.index[0]),
                'count': int(payment_dist.iloc[0]),
                'percentage': round(float(payment_dist.iloc[0]) / len(self.df) * 100, 2),
            }
            
            insights['least_used_payment'] = {
                'method': str(payment_dist.index[-1]),
                'count': int(payment_dist.iloc[-1]),
                'percentage': round(float(payment_dist.iloc[-1]) / len(self.df) * 100, 2),
            }
            
            insights['payment_method_distribution'] = {
                str(k): {
                    'count': int(v),
                    'percentage': round(float(v) / len(self.df) * 100, 2),
                }
                for k, v in payment_dist.items()
            }
            
            # Payment method by revenue
            if 'TotalPrice' in self.df.columns:
                payment_revenue = self.df.groupby('PaymentMethod')['TotalPrice'].sum().sort_values(ascending=False)
                insights['payment_revenue_distribution'] = {
                    str(k): round(float(v), 2) for k, v in payment_revenue.items()
                }
        
        logger.info("Payment insights generated")
        return insights
    
    def generate_referral_insights(self) -> Dict[str, Any]:
        """
        Generate referral-related business insights.
        
        Returns:
            Dict with referral insights.
        """
        insights = {'category': 'Referral Insights'}
        
        if 'ReferralSource' in self.df.columns:
            referral_dist = self.df['ReferralSource'].value_counts()
            
            # Filter out empty strings
            referral_dist = referral_dist[referral_dist.index != '']
            
            if len(referral_dist) > 0:
                insights['best_referral_source'] = {
                    'source': str(referral_dist.index[0]),
                    'count': int(referral_dist.iloc[0]),
                    'percentage': round(float(referral_dist.iloc[0]) / len(self.df) * 100, 2),
                }
                
                insights['lowest_referral_source'] = {
                    'source': str(referral_dist.index[-1]),
                    'count': int(referral_dist.iloc[-1]),
                    'percentage': round(float(referral_dist.iloc[-1]) / len(self.df) * 100, 2),
                }
                
                insights['referral_distribution'] = {
                    str(k): {
                        'count': int(v),
                        'percentage': round(float(v) / len(self.df) * 100, 2),
                    }
                    for k, v in referral_dist.items()
                }
                
                # Referral by revenue
                if 'TotalPrice' in self.df.columns:
                    referral_revenue = self.df.groupby('ReferralSource')['TotalPrice'].sum().sort_values(ascending=False)
                    referral_revenue = referral_revenue[referral_revenue.index != '']
                    insights['referral_revenue_distribution'] = {
                        str(k): round(float(v), 2) for k, v in referral_revenue.items()
                    }
        
        logger.info("Referral insights generated")
        return insights
    
    def generate_all_insights(self) -> Dict[str, Any]:
        """
        Generate all business insights.
        
        Returns:
            Dict with all insight categories.
        """
        logger.info("Generating business insights...")
        
        self.insights = {
            'revenue': self.generate_revenue_insights(),
            'customer': self.generate_customer_insights(),
            'order': self.generate_order_insights(),
            'payment': self.generate_payment_insights(),
            'referral': self.generate_referral_insights(),
            'timestamp': datetime.now().isoformat(),
        }
        
        logger.info("All business insights generated")
        return self.insights.copy()
    
    def save_insights_report(self, output_path: Optional[Path] = None) -> str:
        """
        Save business insights to formatted text report.
        
        Args:
            output_path: Path to save report.
            
        Returns:
            str: Report content.
        """
        output_path = output_path or (config.REPORTS_DIR / 'eda' / 'business_insights.txt')
        
        if not self.insights:
            self.generate_all_insights()
        
        lines = []
        lines.append("=" * 80)
        lines.append(" " * 25 + "BUSINESS INSIGHTS REPORT")
        lines.append(" " * 20 + "Exploratory Data Analysis Framework")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Revenue Insights
        revenue = self.insights.get('revenue', {})
        lines.append("-" * 80)
        lines.append("1. REVENUE INSIGHTS")
        lines.append("-" * 80)
        if 'highest_revenue_product' in revenue:
            lines.append(f"  Total Revenue:               ${revenue.get('total_revenue', 0):,.2f}")
            lines.append(f"  Average Order Value:         ${revenue.get('average_order_value', 0):,.2f}")
            lines.append(f"  Median Order Value:          ${revenue.get('median_order_value', 0):,.2f}")
            lines.append(f"  Highest Revenue Product:     {revenue['highest_revenue_product']['product']} (${revenue['highest_revenue_product']['revenue']:,.2f})")
            lines.append(f"  Lowest Revenue Product:      {revenue['lowest_revenue_product']['product']} (${revenue['lowest_revenue_product']['revenue']:,.2f})")
            lines.append("")
            lines.append("  Top 5 Products by Revenue:")
            for i, (product, rev) in enumerate(revenue.get('top_5_products', {}).items(), 1):
                lines.append(f"    {i}. {product:<20} ${rev:>12,.2f}")
        lines.append("")
        
        # Customer Insights
        customer = self.insights.get('customer', {})
        lines.append("-" * 80)
        lines.append("2. CUSTOMER INSIGHTS")
        lines.append("-" * 80)
        if 'most_active_customer' in customer:
            lines.append(f"  Total Unique Customers:      {customer.get('total_unique_customers', 0):,}")
            lines.append(f"  Most Active Customer:        {customer['most_active_customer']['customer_id']} ({customer['most_active_customer']['order_count']} orders)")
            lines.append(f"  Avg Orders per Customer:     {customer.get('average_orders_per_customer', 0):.2f}")
            if 'highest_value_customer' in customer:
                lines.append(f"  Highest Value Customer:      {customer['highest_value_customer']['customer_id']} (${customer['highest_value_customer']['lifetime_value']:,.2f})")
                lines.append(f"  Avg Customer Lifetime Value: ${customer.get('average_customer_lifetime_value', 0):,.2f}")
        lines.append("")
        
        # Order Insights
        order = self.insights.get('order', {})
        lines.append("-" * 80)
        lines.append("3. ORDER INSIGHTS")
        lines.append("-" * 80)
        if 'order_status_distribution' in order:
            lines.append("  Order Status Distribution:")
            for status, count in order.get('order_status_distribution', {}).items():
                pct = order.get('order_status_percentages', {}).get(status, 0)
                lines.append(f"    {status:<20} {count:>6,} ({pct:>6.2f}%)")
            lines.append(f"  Fulfillment Rate:            {order.get('fulfillment_rate', 0):.2f}%")
            lines.append(f"  Cancellation Rate:           {order.get('cancellation_rate', 0):.2f}%")
            lines.append(f"  Return Rate:                 {order.get('return_rate', 0):.2f}%")
        lines.append("")
        
        # Payment Insights
        payment = self.insights.get('payment', {})
        lines.append("-" * 80)
        lines.append("4. PAYMENT INSIGHTS")
        lines.append("-" * 80)
        if 'most_used_payment' in payment:
            lines.append(f"  Most Used Payment:           {payment['most_used_payment']['method']} ({payment['most_used_payment']['count']:,} orders, {payment['most_used_payment']['percentage']:.2f}%)")
            lines.append(f"  Least Used Payment:          {payment['least_used_payment']['method']} ({payment['least_used_payment']['count']:,} orders, {payment['least_used_payment']['percentage']:.2f}%)")
            lines.append("")
            lines.append("  Payment Method Distribution:")
            for method, info in payment.get('payment_method_distribution', {}).items():
                lines.append(f"    {method:<25} {info['count']:>6,} ({info['percentage']:>6.2f}%)")
        lines.append("")
        
        # Referral Insights
        referral = self.insights.get('referral', {})
        lines.append("-" * 80)
        lines.append("5. REFERRAL INSIGHTS")
        lines.append("-" * 80)
        if 'best_referral_source' in referral:
            lines.append(f"  Best Referral Source:        {referral['best_referral_source']['source']} ({referral['best_referral_source']['count']:,} orders, {referral['best_referral_source']['percentage']:.2f}%)")
            lines.append(f"  Lowest Referral Source:      {referral['lowest_referral_source']['source']} ({referral['lowest_referral_source']['count']:,} orders, {referral['lowest_referral_source']['percentage']:.2f}%)")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF BUSINESS INSIGHTS REPORT")
        lines.append("=" * 80)
        
        report_content = "\n".join(lines)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Business insights report saved to: {output_path}")
        return report_content
    
    def get_insights(self) -> Dict[str, Any]:
        """Get generated insights."""
        if not self.insights:
            self.generate_all_insights()
        return self.insights.copy()
