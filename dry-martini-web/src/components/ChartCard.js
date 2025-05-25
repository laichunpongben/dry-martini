// src/components/ChartCard.js
import React from 'react';
import { Box, Card, CardContent, Typography } from '@mui/material';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';
import annotationPlugin from 'chartjs-plugin-annotation';
import { Chart } from 'chart.js';

Chart.register(annotationPlugin);

export default function ChartCard({ security }) {
  const hasHistory =
    Array.isArray(security.price_history) && security.price_history.length > 0;

  let chartData = null;
  let chartOptions = null;

  if (hasHistory) {
    const labels = security.price_history.map((p) => p.date);
    const dataPoints = security.price_history.map((p) => p.close);

    chartData = {
      labels,
      datasets: [
        {
          data: dataPoints,
          borderColor: '#90caf9',
          fill: false,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 0,
        },
      ],
    };

    chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { top: 4, bottom: 16 },
      },
      scales: {
        x: {
          ticks: { color: '#fff', maxRotation: 0, autoSkipPadding: 20 },
        },
        y: {
          min: Math.min(...dataPoints),
          max: Math.max(...dataPoints),
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
        const ann = chart.options.plugins.annotation.annotations;
        if (elements.length) {
          const { index } = elements[0];
          ann.xLine.value = labels[index];
          ann.yLine.value = dataPoints[index];
        } else {
          ann.xLine.value = null;
          ann.yLine.value = null;
        }
        chart.update('none');
      },
    };
  }

  return (
    <Box sx={{ mb: 0.5, width: '100%', aspectRatio: '1 / 1' }}>
      <Card
        sx={{
          height: '100%',
          bgcolor: 'background.paper',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <CardContent
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            p: 1,
          }}
        >
          {/* Title at the very top */}
          <Box sx={{ mb: 1 }}>
            <Typography
              variant="h6"
              noWrap
              sx={{ color: 'text.primary', fontWeight: 600 }}
              title={security.name}
            >
              {security.name}
            </Typography>
          </Box>

          {/* Metadata Grid */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)', // change to 'repeat(3, 1fr)' for 3 cols
              gap: 1,
              mb: 1,
            }}
          >
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>ISIN:</strong> {security.isin || '–'}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>CUSIP:</strong> {security.cusip || '–'}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>SEDOL:</strong> {security.sedol || '–'}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>Issuer ID:</strong> {security.issuer_id ?? '–'}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>Issue Date:</strong> {security.issue_date ?? '–'}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>Issue Volume:</strong> {security.issue_volume ?? '–'}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>Issue Currency:</strong> {security.issue_currency ?? '–'}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <strong>Maturity:</strong> {security.maturity ?? '–'}
            </Typography>
          </Box>

          {/* Chart or Placeholder */}
          {hasHistory ? (
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'flex-end',
                width: '100%',
              }}
            >
              <Line data={chartData} options={chartOptions} height={null} />
            </Box>
          ) : (
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'text.secondary',
              }}
            >
              <Typography>No price history available</Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
