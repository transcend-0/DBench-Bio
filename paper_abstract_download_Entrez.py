import json
import os
import re
import time
import http.client
import urllib.error
import xml.etree.ElementTree as ET
from Bio import Entrez



def generate_pubmed_query(start_date, end_date, topic=None, journal_list=None, author_list=None, publication_type=None, not_review=True):
    """
    Build a PubMed query string.

    Args:
        journal_list (list): List of journals, e.g. ['Nature', 'Science'].
        author_list (list): List of authors, e.g. ['Smith J', 'Doe J'].
        start_date (str): Start date in YYYY/MM/DD, e.g. '2020/01/01'.
        end_date (str): End date in YYYY/MM/DD, e.g. '2023/12/31'.
        topic (str): Topic keyword, e.g. 'cancer'.

    Returns:
        str: PubMed query string.
    """

    query = f'({start_date}[Date - Entry] : {end_date}[Date - Entry])'
    
    if topic:
        query += f' AND ({topic}[Title/Abstract])'

    if publication_type:
        query += f' AND ({publication_type}[Publication Type])'

    if not_review:
        query += ' NOT (Review[pt] OR systematic[sb] OR "Meta-Analysis"[pt])'

    if journal_list:
        journals_query = ' OR '.join([f'({journal}[Journal])' for journal in journal_list])
        query += f' AND ({journals_query})'

    if author_list:
        authors = [f'({author}[Author])' for author in author_list if isinstance(author, str)]
        authors_with_affiliations = [f'(({author[0]}[Author]) AND "{author[1]}"[Author - Corporate])' for author in author_list if isinstance(author, tuple)]
        authors_query = ' OR '.join(authors + authors_with_affiliations)
        query += f' OR ({authors_query})'

    return query

def _read_handle_with_retry(handle, retries=3, backoff=2):
    last_err = None
    for attempt in range(retries):
        try:
            return handle.read()
        except (http.client.IncompleteRead, urllib.error.HTTPError, urllib.error.URLError, http.client.HTTPException) as err:
            last_err = err
            time.sleep(backoff ** attempt)
    raise last_err


def download_abstract_by_journal(output_path, start_date='2025/12/01', end_date='2025/12/31', journal_list=None, batch_size=200):
    # Build query string
    query = generate_pubmed_query(start_date, end_date, journal_list=journal_list)

    Entrez.email = "your-email@example.com"  # Replace with your email
    Entrez.tool = "MyTool"
    Entrez.api_key = None  # Set if you have an API key

    # Step 1: use esearch to get the PMID list (use history for batched efetch)
    handle = Entrez.esearch(db="pubmed", term=query, usehistory="y", retmax=0)
    record = Entrez.read(handle)
    handle.close()

    count = int(record.get("Count", 0))
    webenv = record.get("WebEnv")
    query_key = record.get("QueryKey")

    print(f"Query from PubMed: {query}")
    print(f"--- Found {count} PMIDs.")

    if count == 0:
        return False

    # Step 2: use efetch to retrieve MEDLINE text in batches to avoid large reads triggering IncompleteRead
    medline_chunks = []
    for start in range(0, count, batch_size):
        handle = Entrez.efetch(
            db="pubmed",
            rettype="medline",
            retmode="text",
            retstart=start,
            retmax=batch_size,
            webenv=webenv,
            query_key=query_key,
        )
        medline_chunks.append(_read_handle_with_retry(handle))
        handle.close()
        time.sleep(0.34)  # NCBI rate limit: without an API key, keep <= ~3 req/s

    medline_data = "".join(medline_chunks)

    papers = []
        
    # 1. Split the entire MEDLINE text into individual record blocks
    records = re.findall(r'(PMID-.*?)(?=\n\n|\Z)', medline_data, re.DOTALL)

    # 2. Compile regex patterns for each field
    title_pattern = re.compile(r'\nTI\s*-\s*(.*?)(?=\n[A-Z]|\Z)', re.DOTALL)
    abstract_pattern = re.compile(r'\nAB\s*-\s*(.*?)(?=\n[A-Z]|\Z)', re.DOTALL)
    date_pattern = re.compile(r'\nEDAT\s*-\s*(.*?)(?=\n[A-Z]|\Z)', re.DOTALL)
    pmid_pattern = re.compile(r'PMID-\s*(\d+)')

    for record in records:
        # 3. Search for fields within each record block
        title_match = title_pattern.search(record)
        abstract_match = abstract_pattern.search(record)
        date_match = date_pattern.search(record)
        pmid_match = pmid_pattern.search(record)

        # 4. Extract and normalize data
        title = None
        if title_match:
            title = re.sub(r'\s+', ' ', title_match.group(1)).strip()

        abstract = None
        if abstract_match:
            abstract = re.sub(r'\s+', ' ', abstract_match.group(1)).strip()

        # Filter out meaningless abstracts
        if abstract is None or abstract.startswith('[This corrects the article'):
            continue

        publication_date = None
        if date_match:
            # "2025/08/28 08:45" -> "2025/08/28"
            publication_date = date_match.group(1).strip().split(' ')[0]

        pmid = pmid_match.group(1).strip() if pmid_match else ""

        # 5. Apply filtering criteria
        if abstract and abstract.endswith('.'):
            papers.append({
                'title': title,
                'abstract': abstract,
                'publication_date': publication_date,
                'pmid': pmid,
            })

    print(f"--- Found {len(papers)} papers with abstracts ending with '.'.")

    # Save as JSON
    print(f"Saving abstracts to {output_path} ...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=4)

    if len(papers) == 0:
        return False

    return True
        
if __name__ == "__main__":
    pass