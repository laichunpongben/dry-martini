// src/components/ChartCard.js
import React from 'react';
import { Box, Card, CardContent, Typography } from '@mui/material';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';
import annotationPlugin from 'chartjs-plugin-annotation';
import { Chart } from 'chart.js';

Chart.register(annotationPlugin);

export default function ChartCard({ security }) {
  if (!security.price_history?.length) return null;

  // prepare data & options
  const labels = security.price_history.map(p => p.date);
  const data = {
    labels,
    datasets: [{
      data: security.price_history.map(p => p.close),
      borderColor: '#90caf9',
      fill: false,
      tension: 0.1,
      pointRadius: 0,
      pointHoverRadius: 0,
    }],
  };
  const options = {
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
          xLine: { type: 'line', scaleID: 'x', value: null, borderWidth: 1, borderDash: [4,4], borderColor: '#90caf9' },
          yLine: { type: 'line', scaleID: 'y', value: null, borderWidth: 1, borderDash: [4,4], borderColor: '#90caf9' },
        },
      },
    },
    onHover: (event, elements, chart) => {
      const ann = chart.options.plugins.annotation.annotations;
      if (elements.length) {
        const { index } = elements[0];
        ann.xLine.value = labels[index];
        ann.yLine.value = data.datasets[0].data[index];
      } else {
        ann.xLine.value = null;
        ann.yLine.value = null;
      }
      chart.update('none');
    },
  };

  return (
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
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'flex-end', width: '100%' }}>
            <Line data={data} options={options} height={null} />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
