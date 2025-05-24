// src/utils/titleCase.js
export const titleCase = (text) =>
  text
    .split('_')
    .map(w => w[0].toUpperCase() + w.slice(1))
    .join(' ');