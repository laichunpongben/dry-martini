-- -------------------------------------------------------------------
-- 1. Create funds table
-- -------------------------------------------------------------------
CREATE TABLE funds (
  id           SERIAL PRIMARY KEY,
  fund_name    TEXT NOT NULL,
  report_date  DATE NOT NULL
);


-- 1) Create issuers table
CREATE TABLE public.issuers (
  id   SERIAL PRIMARY KEY,      -- auto‐incrementing ID :contentReference[oaicite:0]{index=0}
  name TEXT   NOT NULL UNIQUE   -- issuer name must be present and unique :contentReference[oaicite:1]{index=1}
);

-- -------------------------------------------------------------------
-- 2. Create securities table
-- -------------------------------------------------------------------
CREATE TABLE public.securities (
  id             SERIAL PRIMARY KEY,                 -- auto‐incrementing PK :contentReference[oaicite:2]{index=2}
  name           TEXT    NOT NULL,                   -- security name :contentReference[oaicite:3]{index=3}
  cusip          VARCHAR(12),                        -- CUSIP code (up to 12 chars) :contentReference[oaicite:4]{index=4}
  isin           VARCHAR(15),                        -- ISIN code (up to 15 chars) :contentReference[oaicite:5]{index=5}
  sedol          VARCHAR(12),                        -- SEDOL code (up to 12 chars) :contentReference[oaicite:6]{index=6}
  issuer_id      INTEGER REFERENCES public.issuers(id), -- links to issuers table :contentReference[oaicite:7]{index=7}
  issue_date     DATE,                                -- date the security was issued :contentReference[oaicite:8]{index=8}
  issue_volume   NUMERIC,                             -- total issued volume :contentReference[oaicite:9]{index=9}
  issue_currency VARCHAR(3),                          -- ISO currency code, e.g. 'USD' :contentReference[oaicite:10]{index=10}
  maturity       DATE                                 -- maturity date :contentReference[oaicite:11]{index=11}
);

-- -------------------------------------------------------------------
-- 3. Create fund_holdings table
-- -------------------------------------------------------------------
CREATE TABLE fund_holdings (
  id               SERIAL PRIMARY KEY,
  fund_id          INTEGER NOT NULL REFERENCES funds(id),
  security_id      INTEGER NOT NULL REFERENCES securities(id),
  pct_of_portfolio NUMERIC(7,4)
);

-- -------------------------------------------------------------------
-- 4. Enforce uniqueness on individual identifiers
--    (allowing multiple NULLs via partial indexes)
-- -------------------------------------------------------------------

-- 4.1 Non-NULL CUSIP must be unique
CREATE UNIQUE INDEX uniq_securities_cusip
  ON public.securities(cusip)
  WHERE cusip IS NOT NULL;                                         :contentReference[oaicite:0]{index=0}

-- 4.2 Non-NULL ISIN must be unique
CREATE UNIQUE INDEX uniq_securities_isin
  ON public.securities(isin)
  WHERE isin IS NOT NULL;                                          :contentReference[oaicite:1]{index=1}

-- 4.3 Non-NULL SEDOL must be unique
CREATE UNIQUE INDEX uniq_securities_sedol
  ON public.securities(sedol)
  WHERE sedol IS NOT NULL;                                         :contentReference[oaicite:2]{index=2}


CREATE TABLE public.price_history (
    id               SERIAL PRIMARY KEY,
    security_id      INTEGER NOT NULL
                       REFERENCES public.securities(id)
                       ON DELETE CASCADE,
    date             DATE    NOT NULL,
    open             NUMERIC(12,6) NOT NULL,
    close            NUMERIC(12,6) NOT NULL,
    high             NUMERIC(12,6) NOT NULL,
    low              NUMERIC(12,6) NOT NULL,
    volume           INTEGER,            -- 4 bytes instead of 8 bytes
    volume_nominal   INTEGER,            -- also 4 bytes
    UNIQUE(security_id, date)
);

-- Index to speed lookups by security and date
CREATE INDEX idx_price_history_security_date
    ON public.price_history(security_id, date);


CREATE TABLE access_logs (
  id SERIAL PRIMARY KEY,
  security_id INTEGER NOT NULL REFERENCES securities(id),
  accessed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  client_ip INET,
  user_agent TEXT
);


-- Create a view that shows each security’s popularity metrics
CREATE VIEW security_popularity (
  id,
  name,
  isin,
  fund_count,
  access_count,
  doc_count,
  popularity
) AS
SELECT
  s.id,
  s.name,
  s.isin,
  COALESCE(fh.fund_count, 0)   AS fund_count,
  COALESCE(al.access_count, 0) AS access_count,
  COALESCE(doc.doc_count, 0)   AS doc_count,
  (
    COALESCE(fh.fund_count, 0)
    + COALESCE(al.access_count, 0)
    + COALESCE(doc.doc_count, 0)
  ) AS popularity
FROM securities s
LEFT JOIN (
  SELECT security_id, COUNT(DISTINCT fund_id) AS fund_count
  FROM fund_holdings
  GROUP BY security_id
) fh ON fh.security_id = s.id
LEFT JOIN (
  SELECT security_id, COUNT(*) AS access_count
  FROM access_logs
  GROUP BY security_id
) al ON al.security_id = s.id
LEFT JOIN (
  SELECT security_id, COUNT(*) AS doc_count
  FROM documents
  GROUP BY security_id
) doc ON doc.security_id = s.id
ORDER BY popularity DESC;