import js from '@eslint/js';
import remotion from '@remotion/eslint-plugin';
import tseslint from 'typescript-eslint';

export default [
  {ignores: ['node_modules/**', 'jobs/**/out/**', 'out/**']},
  {
    files: ['engine/**/*.{ts,tsx}', 'jobs/**/*.{ts,tsx}', 'job-entry.tsx', 'project-entry.tsx', 'scripts/**/*.{ts,mjs}', 'remotion.config.ts'],
    languageOptions: {parser: tseslint.parser, parserOptions: {ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: {jsx: true}}},
    plugins: {...remotion.flatPlugin.plugins, '@typescript-eslint': tseslint.plugin},
    rules: {
      ...js.configs.recommended.rules,
      ...remotion.flatPlugin.rules,
      'no-undef': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['error', {argsIgnorePattern: '^_', varsIgnorePattern: '^_'}],
      '@remotion/non-pure-animation': 'off',
      '@remotion/slow-css-property': 'off',
      '@remotion/no-object-fit-on-media-video': 'off',
    },
  },
];
