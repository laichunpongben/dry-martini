// src/components/Sidebar.js
import React, { useState } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  List,
  ListItemButton,
  Typography,
  LinearProgress,
  Menu,
  MenuItem
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import SortIcon from '@mui/icons-material/Sort';

export default function Sidebar({
  list,
  filtered,
  search,
  setSearch,
  selectedIsin,
  loadSecurity,
  loading,
  skip,
  lastListItemRef,
  sortMethod,
  setSortMethod
}) {
  const displayList = search ? filtered : list;

  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  const handleClick = (event) => setAnchorEl(event.currentTarget);
  const handleClose = () => setAnchorEl(null);
  const handleSortSelect = (method) => {
    if (method !== sortMethod) setSortMethod(method);
    handleClose();
  };

  return (
    <Box
      sx={{
        width: 420,
        p: 1,
        borderRight: '1px solid #333',
        bgcolor: 'background.paper',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Search bar and sort icon side by side */}
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <TextField
          size="small"
          placeholder="Search ISIN or name"
          value={search}
          onChange={e => setSearch(e.target.value)}
          fullWidth
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
        <IconButton onClick={handleClick} sx={{ ml: 1 }}>
          <SortIcon sx={{ color: 'text.primary' }} />
        </IconButton>
      </Box>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem
          onClick={() => handleSortSelect('popularity')}
          selected={sortMethod === 'popularity'}
        >
          Popularity
        </MenuItem>
        <MenuItem
          onClick={() => handleSortSelect('isin')}
          selected={sortMethod === 'isin'}
        >
          ISIN
        </MenuItem>
        <MenuItem
          onClick={() => handleSortSelect('name')}
          selected={sortMethod === 'name'}
        >
          Name
        </MenuItem>
        <MenuItem
          onClick={() => handleSortSelect('issue_date')}
          selected={sortMethod === 'issue_date'}
        >
          New Issue
        </MenuItem>
      </Menu>

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
