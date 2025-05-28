import pandas as pd
from thefuzz import fuzz, process
from io import BytesIO

def match_linkedin_bullhorn(file1, file2, fuzzy_threshold_company=60, fuzzy_threshold_role=60):
    # Read CSVs
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Identify format
    def is_linkedin(df):
        return 'First Name' in df.columns and 'Last Name' in df.columns

    def is_bullhorn(df):
        return 'Naam' in df.columns and 'Huidige functietitel' in df.columns

    def process_li(df):
        df = df.copy()
        df['Naam'] = df['First Name'].astype(str).str.strip() + ' ' + df['Last Name'].astype(str).str.strip()
        return df[['Naam', 'Position', 'Company']].rename(columns={
            'Position': 'functie',
            'Company': 'bedrijf'
        })

    def process_bh(df):
        df = df.copy()
        return df[['Naam', 'Huidige functietitel', 'Bedrijf']].rename(columns={
            'Huidige functietitel': 'functie',
            'Bedrijf': 'bedrijf'
        })

    # Detect and process both files
    if is_linkedin(df1):
        df1_processed = process_li(df1)
    elif is_bullhorn(df1):
        df1_processed = process_bh(df1)
    else:
        raise ValueError("File 1 is not recognized as LinkedIn or Bullhorn format.")

    if is_linkedin(df2):
        df2_processed = process_li(df2)
    elif is_bullhorn(df2):
        df2_processed = process_bh(df2)
    else:
        raise ValueError("File 2 is not recognized as LinkedIn or Bullhorn format.")

    # Rename for clarity
    df1_processed = df1_processed.rename(columns={'functie': 'functie_1', 'bedrijf': 'bedrijf_1'})
    df2_processed = df2_processed.rename(columns={'functie': 'functie_2', 'bedrijf': 'bedrijf_2'})

    # Clean names
    df1_processed['Naam'] = df1_processed['Naam'].astype(str).str.strip()
    df2_processed['Naam'] = df2_processed['Naam'].astype(str).str.strip()

    # Fuzzy match names
    names_1 = df1_processed['Naam'].tolist()
    df2_processed['match_result'] = df2_processed['Naam'].apply(
        lambda name: process.extractOne(name, names_1, scorer=fuzz.token_set_ratio)
    )
    df2_processed[['matched_name', 'match_score']] = pd.DataFrame(df2_processed['match_result'].tolist(), index=df2_processed.index)
    matched_df = df2_processed[df2_processed['match_score'] >= 90].copy()

    # Merge info from both datasets
    merged_df = matched_df.merge(
        df1_processed, left_on='matched_name', right_on='Naam', how='inner', suffixes=('_2', '_1')
    )

    # Normalize for fuzzy comparison
    for col in ['bedrijf_1', 'bedrijf_2', 'functie_1', 'functie_2']:
        merged_df[col] = merged_df[col].astype(str).str.lower().str.strip()

    # Fuzzy scores
    merged_df['bedrijf_score'] = merged_df.apply(
        lambda x: fuzz.token_set_ratio(x['bedrijf_1'], x['bedrijf_2']), axis=1
    )
    merged_df['functie_score'] = merged_df.apply(
        lambda x: fuzz.token_set_ratio(x['functie_1'], x['functie_2']), axis=1
    )

    # Match flags
    merged_df['bedrijf_match'] = merged_df['bedrijf_score'] >= fuzzy_threshold_company
    merged_df['functie_match'] = merged_df['functie_score'] >= fuzzy_threshold_role

    # Categorization
    same_company_new_role = merged_df[merged_df['bedrijf_match'] & ~merged_df['functie_match']][
        ['Naam_2', 'bedrijf_2', 'functie_1', 'functie_2']
    ].rename(columns={
        'Naam_2': 'Naam',
        'bedrijf_2': 'Bedrijf',
        'functie_1': 'Oude rol',
        'functie_2': 'Nieuwe rol'
    })

    same_role_new_company = merged_df[~merged_df['bedrijf_match'] & merged_df['functie_match']][
        ['Naam_2', 'bedrijf_1', 'bedrijf_2', 'functie_2']
    ].rename(columns={
        'Naam_2': 'Naam',
        'bedrijf_1': 'Oud bedrijf',
        'bedrijf_2': 'Nieuw bedrijf',
        'functie_2': 'Rol'
    })

    different_both = merged_df[~merged_df['bedrijf_match'] & ~merged_df['functie_match']][
        ['Naam_2', 'bedrijf_1', 'bedrijf_2', 'functie_1', 'functie_2']
    ].rename(columns={
        'Naam_2': 'Naam',
        'bedrijf_1': 'Oud bedrijf',
        'bedrijf_2': 'Nieuw bedrijf',
        'functie_1': 'Oude functie',
        'functie_2': 'Nieuwe functie'
    })

    # Write to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        same_company_new_role.to_excel(writer, sheet_name='Nieuwe rol, Zelfde bedrijf', index=False)
        same_role_new_company.to_excel(writer, sheet_name='Zelfde rol, Nieuw bedrijf', index=False)
        different_both.to_excel(writer, sheet_name='Niuewe rol & bedrijf', index=False)
    output.seek(0)
    return output
