import pandas as pd
from thefuzz import fuzz
from thefuzz import process
from io import BytesIO

def match_linkedin_bullhorn(file1, file2, fuzzy_threshold_company=60, fuzzy_threshold_role=60):
    # Read CSVs
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Helper functions
    def is_linkedin(df):
        return 'First Name' in df.columns and 'Last Name' in df.columns

    def process_li(df):
        df = df.copy()
        df['Naam'] = df['First Name'].astype(str).str.strip() + ' ' + df['Last Name'].astype(str).str.strip()
        return df[['Naam', 'Position', 'Company']].rename(columns={
            'Position': 'functie_LI',
            'Company': 'bedrijf_LI'
        })

    def process_bh(df):
        df = df.copy()
        return df[['Naam', 'Huidige functietitel', 'Bedrijf']].rename(columns={
            'Huidige functietitel': 'functie_BH',
            'Bedrijf': 'bedrijf_BH'
        })

    # Identify and process LI/BH
    if is_linkedin(df1):
        li_df = process_li(df1)
        bh_df = process_bh(df2)
    else:
        li_df = process_li(df2)
        bh_df = process_bh(df1)

    # Clean names
    li_df['Naam'] = li_df['Naam'].str.strip()
    bh_df['Naam'] = bh_df['Naam'].astype(str).str.strip()

    # Find common names with fuzzy matching
    li_names = li_df['Naam'].tolist()
    bh_df['match_result'] = bh_df['Naam'].apply(lambda name: process.extractOne(name, li_names, scorer=fuzz.token_set_ratio))
    bh_df[['matched_name', 'match_score']] = pd.DataFrame(bh_df['match_result'].tolist(), index=bh_df.index)
    matched_df = bh_df[bh_df['match_score'] >= 90].copy()

    # Merge matched data from both sources
    merged_df = matched_df.merge(
        li_df, left_on='matched_name', right_on='Naam', how='inner', suffixes=('_BH', '_LI')
    )

    # Prepare for fuzzy comparison
    for col in ['bedrijf_BH', 'bedrijf_LI', 'functie_BH', 'functie_LI']:
        merged_df[col] = merged_df[col].astype(str).str.lower().str.strip()

    # Fuzzy similarity scores
    merged_df['bedrijf_score'] = merged_df.apply(
        lambda x: fuzz.token_set_ratio(x['bedrijf_BH'], x['bedrijf_LI']), axis=1
    )
    merged_df['functie_score'] = merged_df.apply(
        lambda x: fuzz.token_set_ratio(x['functie_BH'], x['functie_LI']), axis=1
    )

    # Match flags
    merged_df['bedrijf_match'] = merged_df['bedrijf_score'] >= fuzzy_threshold_company
    merged_df['functie_match'] = merged_df['functie_score'] >= fuzzy_threshold_role

    # Categorize matches
    same_company_new_role = merged_df[merged_df['bedrijf_match'] & ~merged_df['functie_match']][
        ['Naam_BH', 'bedrijf_BH', 'functie_BH', 'functie_LI']
    ].rename(columns={
        'Naam_BH': 'Naam',
        'bedrijf_BH': 'Company',
        'functie_BH': 'Old Role',
        'functie_LI': 'New Role'
    })

    same_role_new_company = merged_df[~merged_df['bedrijf_match'] & merged_df['functie_match']][
        ['Naam_BH', 'bedrijf_BH', 'bedrijf_LI', 'functie_BH']
    ].rename(columns={
        'Naam_BH': 'Naam',
        'bedrijf_BH': 'Old Company',
        'bedrijf_LI': 'New Company',
        'functie_BH': 'Role'
    })

    different_both = merged_df[~merged_df['bedrijf_match'] & ~merged_df['functie_match']][
        ['Naam_BH', 'bedrijf_BH', 'bedrijf_LI', 'functie_BH', 'functie_LI']
    ].rename(columns={
        'Naam_BH': 'Naam',
        'bedrijf_BH': 'Old Company',
        'bedrijf_LI': 'New Company',
        'functie_BH': 'Old Role',
        'functie_LI': 'New Role'
    })

    # Export to Excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        same_company_new_role.to_excel(writer, sheet_name='New Role, Same Company', index=False)
        same_role_new_company.to_excel(writer, sheet_name='Same Role, New Company', index=False)
        different_both.to_excel(writer, sheet_name='Different Role & Company', index=False)
    output.seek(0)
    return output


