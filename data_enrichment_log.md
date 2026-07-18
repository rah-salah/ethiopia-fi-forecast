# Data Enrichment Log

This log documents all additions made to `data/raw/ethiopia_fi_unified_data.csv` beyond the original 57-record dataset, following the project's unified schema.

---

## REC_0034 — Mobile Phone Ownership Rate

- **Value:** 58% of adults (national, all genders, 2024)
- **New indicator:** not previously tracked in the dataset (the existing `GEN_GAP_MOBILE` record only captures the gender *gap* in mobile ownership, not the overall national rate)
- **source_url:** https://rsisinternational.org/journals/ijrsi/uploads/vol12-iss10-pg3863-3872-202511_pdf.pdf
- **original_text:** "the ownership rate in Ethiopia is significantly lower at 58%, vs 81% in Sub-Saharan Africa"
- **confidence:** medium (secondary academic paper citing Global Findex 2025 microdata, not the primary Findex report itself)
- **collected_by:** Rahma_Salah
- **collection_date:** see CSV `collection_date` column
- **Why useful:** Mobile phone ownership is a structural prerequisite for mobile money and digital account access. Having this as a standalone indicator lets Task 2/4 analysis test how much of Ethiopia's account-ownership ceiling is explained by device access rather than service availability.

## REC_0035 & REC_0036 — Precise Gender-Disaggregated Account Ownership, 2024

- **Values:** Male 56.53%, Female 41.62% (national, 2024)
- **source_url:** https://rsisinternational.org/journals/ijrsi/uploads/vol12-iss10-pg3863-3872-202511_pdf.pdf
- **original_text:** "men (56.53%) ... women in Ethiopia (41.62%)"
- **confidence:** medium
- **collected_by:** Rahma_Salah
- **collection_date:** see CSV `collection_date` column
- **Why useful:** The existing dataset's 2024 gender split (REC_0004/REC_0005) is only available for 2021; the 2024 update (REC_0006) has no gender breakdown at all. These two records fill that gap with precisely sourced 2024 figures, enabling an accurate 2024 gender-gap calculation (see REC_0037).

## REC_0037 — Precise Account Ownership Gender Gap, 2024

- **Value:** 14.91 percentage points (56.53% male − 41.62% female)
- **source_url:** https://rsisinternational.org/journals/ijrsi/uploads/vol12-iss10-pg3863-3872-202511_pdf.pdf
- **original_text:** "56.53% male vs 41.62% female = 14.91pp gap" (derived from REC_0035/REC_0036)
- **confidence:** high (directly computed from precisely sourced figures, vs. the existing REC_0028's "estimated ~18pp")
- **collected_by:** Rahma_Salah
- **collection_date:** see CSV `collection_date` column
- **Why useful:** Replaces a medium-confidence estimate with a precisely sourced value, improving the reliability of any gender-gap trend analysis or forecasting that uses this indicator.

## REC_0038 — Digital Payment Adoption Rate

- **Value:** 16% of adults (national, 2024)
- **New indicator:** distinct from the existing operator-reported transaction counts (e.g. `USG_P2P_COUNT`, `USG_TELEBIRR_USERS`), this is a survey-based measure of the *share of adults* who have adopted any digital payment method
- **source_url:** https://rsisinternational.org/journals/ijrsi/uploads/vol12-iss10-pg3863-3872-202511_pdf.pdf
- **original_text:** "low levels of digital payments (16 percent)"
- **confidence:** medium
- **collected_by:** Rahma_Salah
- **collection_date:** see CSV `collection_date` column
- **Why useful:** Operator transaction counts (e.g. Telebirr's 54.84M registered users) can overstate genuine adoption breadth since they don't distinguish active from dormant users at the population level. This survey-based adoption rate provides an independent, population-level cross-check.

---

## Data Point Considered but NOT Added: 2011 Baseline

While researching a 2011 Global Findex account-ownership baseline for Ethiopia (several secondary sources reference "22% in 2011"), we traced this to an authoritative World Bank source stating the 22% figure is actually the **2014** baseline, and confirmed via the Global Findex 2014 report that **Ethiopia was not included in the 2011 Global Findex survey wave at all** — it was added starting in the 2014 edition. No genuine 2011 data point exists for Ethiopia, so none was fabricated. This is documented as a data limitation in the EDA notebook rather than invented.

- Corroborating source (confirms 22% = 2014, not 2011): https://www.worldbank.org/en/news/feature/2019/10/03/leveraging-national-statistics-agencies-and-country-owned-surveys-for-financial-inclusion-measurement-ethiopia
- Corroborating source (confirms Ethiopia added in the 2014 edition): https://gflec.org/wp-content/uploads/2015/09/GlobalFindex2015.pdf
