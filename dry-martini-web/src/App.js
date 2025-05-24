import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';
import { Chart } from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItemButton,
  Divider,
  TextField,
  InputAdornment,
  IconButton,
  LinearProgress,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

Chart.register(annotationPlugin);

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: { default: '#121212', paper: '#1e1e1e' },
    primary: { main: '#90caf9' },
    text: { primary: '#fff', secondary: '#bbb' },
  },
});

const titleCase = text =>
  text
    .split('_')
    .map(w => w[0].toUpperCase() + w.slice(1))
    .join(' ');

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

  const limit = 100;
  const backend = process.env.REACT_APP_BACKEND_URL || 'http://localhost:6010';

  // IntersectionObserver for infinite scroll (only when not filtering)
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

  // Fetch paginated list, dedupe by ISIN
  useEffect(() => {
    setLoading(true);
    fetch(`${backend}/securities?skip=${skip}&limit=${limit}`)
      .then(r => {
        if (!r.ok) throw new Error('Failed to load securities');
        return r.json();
      })
      .then(newItems => {
        setList(prev => {
          const existing = new Set(prev.map(i => i.isin));
          const unique = newItems.filter(item => !existing.has(item.isin));
          return [...prev, ...unique];
        });
        setHasMore(newItems.length === limit);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [skip, backend]);

  // Set title on mount
  useEffect(() => {
    document.title = 'Bond Explorer';
  }, []);

  // Load detail for one security
  const loadSecurity = isin => {
    setLoading(true);
    setError(null);
    setSecurity(null);
    setSelectedDoc(null);
    setSelectedIsin(isin);

    fetch(`${backend}/securities/${isin}`)
      .then(r => {
        if (!r.ok) throw new Error('Not found');
        return r.json();
      })
      .then(async data => {
        setSecurity(data);
        setSelectedDoc(data.documents[0] || null);
        const newCache = {};
        await Promise.all(
          data.documents.map(async doc => {
            try {
              const res = await fetch(doc.url);
              const blob = await res.blob();
              newCache[doc.id] = URL.createObjectURL(blob);
            } catch {
              newCache[doc.id] = doc.url;
            }
          })
        );
        setBlobCache(newCache);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  // Filtered view
  const filtered = list.filter(
    s =>
      s.isin.includes(search.toUpperCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <ThemeProvider theme={darkTheme}>
      <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
        {/* Left Panel: Search + List */}
        <Box
          sx={{
            width: 280,
            p: 1,
            borderRight: '1px solid #333',
            bgcolor: 'background.paper',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <TextField
            size="small"
            placeholder="Search ISIN or name"
            value={search}
            onChange={e => setSearch(e.target.value)}
            InputProps={{
              sx: { bgcolor: 'background.default', color: 'text.primary' },
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton>
                    <SearchIcon sx={{ color: 'text.primary' }} />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Box sx={{ flex: 1, overflowY: 'auto', mt: 1, '&::-webkit-scrollbar': { display: 'none' } }}>
            <List disablePadding>
              {(search ? filtered : list).map((s, idx) => (
                <Box
                  key={s.isin}
                  sx={{ position: 'relative' }}
                  ref={!search && idx === list.length - 1 ? lastListItemRef : null}
                >
                  <ListItemButton
                    selected={selectedIsin === s.isin}
                    onClick={() => loadSecurity(s.isin)}
                    sx={{ py: 0.5 }}
                  >
                    <Typography noWrap variant="body2" sx={{ color: 'text.primary', width: '100%' }}>
                      {s.isin} - {s.name}
                    </Typography>
                  </ListItemButton>
                  {loading && selectedIsin === s.isin && (
                    <LinearProgress sx={{ position: 'absolute', bottom: 0, left: 0, right: 0 }} />
                  )}
                </Box>
              ))}
              {loading && !search && skip > 0 && <LinearProgress />}
            </List>
          </Box>
        </Box>

        {/* Center Panel: Details + Documents */}
        <Box sx={{ width: 540, p: 2, overflowY: 'auto', bgcolor: 'background.default' }}>
          {error && (
            <Typography color="error" align="center">
              {error}
            </Typography>
          )}

          {security && (
            <Box sx={{ mb: 2, width: '100%', aspectRatio: '1 / 1' }}>
              <Card sx={{ height: '100%', bgcolor: 'background.paper', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', pb: 0 }}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="h5" sx={{ color: 'text.primary', mb: 1 }}>
                      {security.name}
                    </Typography>
                    <Typography variant="body1" sx={{ color: 'text.secondary' }}>
                      <strong>ISIN:</strong> {security.isin}
                    </Typography>
                    <Typography variant="body1" sx={{ color: 'text.secondary' }}>
                      <strong>CUSIP:</strong> {security.cusip || '–'}
                    </Typography>
                    <Typography variant="body1" sx={{ color: 'text.secondary' }}>
                      <strong>SEDOL:</strong> {security.sedol || '–'}
                    </Typography>
                  </Box>

                  {/* Price Chart with hover-helping lines */}
                  {security.price_history?.length > 0 && (
                    <Box sx={{ flex: 1, display: 'flex', alignItems: 'flex-end', width: '100%' }}>
                      <Line
                        data={{
                          labels: security.price_history.map(p => p.date),
                          datasets: [
                            {
                              data: security.price_history.map(p => p.close),
                              borderColor: '#90caf9',
                              fill: false,
                              tension: 0.1,
                              pointRadius: 0,
                              pointHoverRadius: 0,
                            },
                          ],
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          scales: {
                            x: { ticks: { color: '#fff', maxRotation: 0, autoSkipPadding: 20 } },
                            y: {
                              min: Math.min(...security.price_history.map(p => p.close)),
                              max: Math.max(...security.price_history.map(p => p.close)),
                              ticks: { color: '#fff' },
                            },
                          },
                          plugins: {
                            legend: { display: false },
                            tooltip: { mode: 'index', intersect: false },
                            annotation: {
                              annotations: {
                                xLine: {
                                  type: 'line',
                                  scaleID: 'x',
                                  value: null,
                                  borderWidth: 1,
                                  borderDash: [4, 4],
                                  borderColor: '#90caf9',
                                },
                                yLine: {
                                  type: 'line',
                                  scaleID: 'y',
                                  value: null,
                                  borderWidth: 1,
                                  borderDash: [4, 4],
                                  borderColor: '#90caf9',
                                },
                              },
                            },
                          },
                          onHover: (event, elements, chart) => {
                            if (elements.length) {
                              const { index } = elements[0];
                              const xVal = chart.data.labels[index];
                              const yVal = chart.data.datasets[0].data[index];
                              chart.options.plugins.annotation.annotations.xLine.value = xVal;
                              chart.options.plugins.annotation.annotations.yLine.value = yVal;
                            } else {
                              chart.options.plugins.annotation.annotations.xLine.value = null;
                              chart.options.plugins.annotation.annotations.yLine.value = null;
                            }
                            chart.update('none');
                          },
                        }}
                        height={null}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Documents List */}
          {security && (
            <Box>
              <Typography variant="h6" sx={{ color: 'text.primary', mb: 1 }}>
                Documents
              </Typography>
              <List disablePadding>
                {security.documents.map(doc => (
                  <React.Fragment key={doc.id}>
                    <ListItemButton
                      selected={selectedDoc?.id === doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      sx={{ py: 0.5 }}
                    >
                      <Typography sx={{ color: 'text.primary' }}>{titleCase(doc.doc_type)}</Typography>
                    </ListItemButton>
                    <Divider sx={{ bgcolor: '#333' }} />
                  </React.Fragment>
                ))}
              </List>
            </Box>
          )}
        </Box>

        {/* Right Panel: PDF Viewer */}
        <Box sx={{ flex: 1, p: 2, bgcolor: 'background.default' }}>
          {selectedDoc && (
            <Box
              component="iframe"
              src={blobCache[selectedDoc.id] || selectedDoc.url}
              sx={{ width: '100%', height: '100%', border: 'none' }}
            />
          )}
        </Box>
      </Box>
    </ThemeProvider>
  );
}
