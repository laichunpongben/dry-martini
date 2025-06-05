// src/App.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ThemeProvider, Box, Typography } from '@mui/material';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ChartCard from './components/ChartCard';
import SummaryPanel from './components/SummaryPanel';
import DocumentsPanel from './components/DocumentsPanel';
import PdfViewer from './components/PdfViewer';
import FundHoldingsPanel from './components/FundHoldingsPanel';
import { darkTheme, lightTheme } from './theme';

export default function App() {
  const [list, setList] = useState([]);
  const [security, setSecurity] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [blobCache, setBlobCache] = useState({});
  const [selectedIsin, setSelectedIsin] = useState(null);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [sortMethod, setSortMethod] = useState('popularity');
  const [mode, setMode] = useState('dark');

  const theme = mode === 'dark' ? darkTheme : lightTheme;

  const securityCache = useRef({});
  const limit = 100;
  const backend = process.env.REACT_APP_BACKEND_URL || 'http://localhost:6010';

  const observer = useRef();
  const lastListItemRef = useCallback(node => {
    if (loading || search) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setSkip(prev => prev + limit);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore, search]);

  useEffect(() => {
    setLoading(true);
    setList([]);
    setSkip(0);
    setHasMore(true);
  }, [sortMethod, search]);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ skip, limit });
    if (!search) params.set('sort', sortMethod);
    fetch(`${backend}/securities?${params.toString()}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(newItems => {
        setList(prev => {
          const existing = new Set(prev.map(i => i.isin));
          return [...prev, ...newItems.filter(item => !existing.has(item.isin))];
        });
        setHasMore(newItems.length === limit);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [skip, sortMethod, search, backend]);

  useEffect(() => {
    document.title = 'Bond Explorer';
  }, []);

  const loadSecurity = async (isin, idx) => {
    setError(null);
    setSelectedDoc(null);
    setSelectedIsin(isin);

    if (securityCache.current[isin]) {
      setSecurity(securityCache.current[isin]);
    } else {
      setLoading(true);
      try {
        const r = await fetch(`${backend}/securities/${isin}`);
        if (!r.ok) throw new Error('Not found');
        const data = await r.json();
        securityCache.current[isin] = data;
        setSecurity(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }

    const next = list[idx + 1];
    if (next && !securityCache.current[next.isin]) {
      fetch(`${backend}/securities/${next.isin}`)
        .then(r2 => r2.ok && r2.json())
        .then(d2 => { if (d2) securityCache.current[next.isin] = d2; })
        .catch(() => {});
    }
  };

  const onDocumentClick = async doc => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(doc.url);
      if (!res.ok) throw new Error('Failed to fetch document');
      const blob = await res.blob();
      setBlobCache(prev => ({ ...prev, [doc.id]: URL.createObjectURL(blob) }));
      setSelectedDoc(doc);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const filtered = list.filter(
    s =>
      s.isin.includes(search.toUpperCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase())
  );

  const toggleMode = () =>
    setMode(prev => (prev === 'dark' ? 'light' : 'dark'));

  return (
    <ThemeProvider theme={theme}>
      <TopBar mode={mode} toggleMode={toggleMode} />

      <Box sx={{ display: 'flex', height: 'calc(100vh - 48px)', bgcolor: 'background.default' }}>
        <Sidebar
          list={list}
          filtered={filtered}
          search={search}
          setSearch={setSearch}
          selectedIsin={selectedIsin}
          loadSecurity={loadSecurity}
          loading={loading}
          skip={skip}
          lastListItemRef={lastListItemRef}
          sortMethod={sortMethod}
          setSortMethod={setSortMethod}
        />

        <Box sx={{ width: 600, p: 1, overflowY: 'auto', bgcolor: 'background.default' }}>
          {error && (
            <Typography color="error" align="center">
              {error}
            </Typography>
          )}

          {security && <ChartCard security={security} />}

          {/* Summary Panel */}
          {security && <SummaryPanel summary={security.summary} />}

          {security && (
            <DocumentsPanel
              security={security}
              selectedDoc={selectedDoc}
              onDocumentClick={onDocumentClick}
            />
          )}

          {security && (
            <FundHoldingsPanel holdings={security.fund_holdings} />
          )}
        </Box>

        <Box sx={{ flex: 1, p: 1, bgcolor: 'background.default' }}>
          <PdfViewer selectedDoc={selectedDoc} blobCache={blobCache} />
        </Box>
      </Box>
    </ThemeProvider>
  );
}