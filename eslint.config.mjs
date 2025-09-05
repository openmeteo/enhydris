import path from 'node:path';
import globals from 'globals';

import { includeIgnoreFile } from '@eslint/compat';
import js from '@eslint/js';
// eslint-disable-next-line import/no-unresolved
import { configs } from 'eslint-config-airbnb-extended/legacy';

const gitignorePath = path.resolve('.', '.gitignore');

const jsConfig = [
  {
    name: 'js/config',
    ...js.configs.recommended,
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.jquery,
        enhydris: 'writeable',
        google: 'readonly',
        moment: 'readonly',
        L: 'readonly',
        ApexCharts: 'readonly',
        Chart: 'readonly',
        Arg: 'readonly',
        axios: 'readonly',
      },
    },
  },
  ...configs.base.recommended,
  {
    files: ['**/*.test.js'],
    languageOptions: {
      sourceType: 'commonjs',
      globals: {
        ...globals.jest,
      },
    },
  },
];

export default [
  {
    ignores: [
      '**/js/vendor/**',
    ],
  },
  includeIgnoreFile(gitignorePath),
  ...jsConfig,
];
