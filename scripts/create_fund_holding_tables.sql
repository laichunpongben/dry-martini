-- -------------------------------------------------------------------
-- 1. Create funds table
-- -------------------------------------------------------------------
CREATE TABLE funds (
  id           SERIAL PRIMARY KEY,
  fund_name    TEXT NOT NULL,
  report_date  DATE NOT NULL
);

-- -------------------------------------------------------------------
-- 2. Create securities table
-- -------------------------------------------------------------------
CREATE TABLE securities (
  id    SERIAL PRIMARY KEY,
  name  TEXT NOT NULL,
  cusip VARCHAR(12),
  isin  VARCHAR(15),
  sedol VARCHAR(12)
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