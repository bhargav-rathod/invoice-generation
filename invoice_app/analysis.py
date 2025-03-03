import pandas as pd
import matplotlib.pyplot as plt
from database import fetch_non_archived_data

def plot_total_sales():
    invoices_df, _ = fetch_non_archived_data()
    invoices_df["date_time"] = pd.to_datetime(invoices_df["date_time"])
    invoices_df["month"] = invoices_df["date_time"].dt.to_period("M")
    invoices_df["year"] = invoices_df["date_time"].dt.to_period("Y")
    
    monthly_sales = invoices_df.groupby("month")["total"].sum()
    yearly_sales = invoices_df.groupby("year")["total"].sum()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    monthly_sales.plot(kind="bar", ax=ax1, color="skyblue")
    ax1.set_title("Monthly Sales")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Total Sales")
    
    yearly_sales.plot(kind="bar", ax=ax2, color="lightgreen")
    ax2.set_title("Yearly Sales")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Total Sales")
    
    plt.tight_layout()
    plt.show()

def plot_item_wise_sales():
    _, items_df = fetch_non_archived_data()
    items_df["total_amount"] = items_df["quantity"] * items_df["price"]
    item_wise_sales = items_df.groupby("product")["total_amount"].sum()
    
    plt.figure(figsize=(8, 5))
    item_wise_sales.plot(kind="bar", color="orange")
    plt.title("Item-wise Sales")
    plt.xlabel("Product")
    plt.ylabel("Total Amount")
    plt.tight_layout()
    plt.show()

def plot_highest_lowest():
    invoices_df, _ = fetch_non_archived_data()
    highest = invoices_df["total"].max()
    lowest = invoices_df["total"].min()
    
    plt.figure(figsize=(6, 4))
    plt.bar(["Highest", "Lowest"], [highest, lowest], color=["green", "red"])
    plt.title("Highest and Lowest Sales")
    plt.ylabel("Amount")
    plt.tight_layout()
    plt.show()

def plot_monthly_increase():
    invoices_df, _ = fetch_non_archived_data()
    invoices_df["date_time"] = pd.to_datetime(invoices_df["date_time"])
    invoices_df["month"] = invoices_df["date_time"].dt.to_period("M")
    
    monthly_sales = invoices_df.groupby("month")["total"].sum()
    monthly_increase = monthly_sales.diff().fillna(0)
    
    plt.figure(figsize=(8, 5))
    monthly_increase.plot(kind="bar", color="purple")
    plt.title("Monthly Increase in Sales")
    plt.xlabel("Month")
    plt.ylabel("Increase in Sales")
    plt.tight_layout()
    plt.show()