# !! Before Run Project Install Pandas library with command: pip install pandas
import pandas as pd
import json
from datetime import datetime, timedelta

# Load data
data = pd.read_csv('data.csv')

# Function to parse dates
def parse_date(date_str, date_format):
    try:
        return datetime.strptime(date_str, date_format)
    except ValueError:
        return None

# function for calculations
def calculate_features(contracts, application_date):
    tot_claim_cnt_l180d = -3
    disb_bank_loan_wo_tbc = -1
    day_sinlastloan = -3

    if pd.notna(contracts):  # Check if contracts exists
            contracts_list = json.loads(contracts)
            if not isinstance(contracts_list, list):
                contracts_list = [contracts_list]

            claims = [c for c in contracts_list if 'claim_date']
            loans = [c for c in contracts_list if 'contract_date' and 'summa']

            # Parse application date and remove timezone information
            application_date_dt = parse_date(application_date, '%Y-%m-%d %H:%M:%S.%f%z')
            if not application_date_dt:
                return tot_claim_cnt_l180d, disb_bank_loan_wo_tbc, day_sinlastloan

            application_date_naive = application_date_dt.replace(tzinfo=None)

            # 1: tot_claim_cnt_l180d
            if claims:
                recent_claims = [
                    c for c in claims
                    if parse_date(c['claim_date'], '%d.%m.%Y') and
                       parse_date(c['claim_date'], '%d.%m.%Y') >= application_date_naive - timedelta(days=180)
                ]
                tot_claim_cnt_l180d = len(recent_claims) if recent_claims else -3

            # 2: disb_bank_loan_wo_tbc
            if loans:
                filtered_loans = [
                    c for c in loans if 'bank' in c and c['bank'] not in ['LIZ', 'LOM', 'MKO', 'SUG', None]
                ]
                disbursed_sum = sum(float(c['loan_summa']) for c in filtered_loans if c['loan_summa'])
                disb_bank_loan_wo_tbc = disbursed_sum if filtered_loans else -3

            # 3: day_sinlastloan
            if loans:
                valid_loans = [
                    parse_date(c['contract_date'], '%d.%m.%Y') for c in loans if parse_date(c['contract_date'], '%d.%m.%Y')
                ]
                if valid_loans:
                    last_loan_date = max(valid_loans)
                    day_sinlastloan = (application_date_naive - last_loan_date).days

    return tot_claim_cnt_l180d, disb_bank_loan_wo_tbc, day_sinlastloan

# calculation of features
data[['tot_claim_cnt_l180d', 'disb_bank_loan_wo_tbc', 'day_sinlastloan']] = data.apply(
    lambda row: calculate_features(row['contracts'], row['application_date']), axis=1, result_type='expand'
)

# Save the output
data.to_csv('contract_features.csv', index=False)

print('Feature calculation completed and saved to contract_features.csv')