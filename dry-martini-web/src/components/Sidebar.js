// src/components/Sidebar.js
import React from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  List,
  ListItemButton,
  Typography,
  LinearProgress,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

export default function Sidebar({
  list,
  filtered,
  search,
  setSearch,
  selectedIsin,
  loadSecurity,
  loading,
  skip,
  lastListItemRef
}) {
  const displayList = search ? filtered : list;

  return (
    <Box
      sx={{
        width: 420,               // increased from 280 to 420 (50% wider)
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

      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          mt: 1,
          '&::-webkit-scrollbar': { display: 'none' },
        }}
      >
        <List disablePadding>
          {displayList.map((s, idx) => (
            <Box
              key={s.isin}
              sx={{ position: 'relative' }}
              ref={!search && idx === list.length - 1 ? lastListItemRef : null}
            >
              <ListItemButton
                selected={selectedIsin === s.isin}
                onMouseEnter={() => loadSecurity(s.isin, idx)}
                sx={{ py: 0.5 }}
              >
                <Typography
                  noWrap
                  variant="body2"
                  sx={{ color: 'text.primary', width: '100%' }}
                >
                  {s.isin} – {s.name}
                </Typography>
              </ListItemButton>
              {loading && selectedIsin === s.isin && (
                <LinearProgress
                  sx={{ position: 'absolute', bottom: 0, left: 0, right: 0 }}
                />
              )}
            </Box>
          ))}
          {loading && !search && skip > 0 && <LinearProgress />}
        </List>
      </Box>
    </Box>
  );
}
