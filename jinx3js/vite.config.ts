/**
 * Vite config for the Jinx viewer.
 *
 * `base: './'` keeps the built bundle relocatable, which is what lets
 * `tools/render.mjs` serve `dist/` from a throwaway in-process static server
 * without caring about the mount path.
 *
 * `publicDir` is off: the viewer ships no runtime assets at all -- the geometry
 * is compiled into the bundle by `tools/bake.ts`, and the one image on the page
 * (the source-reference thumbnail) is imported from `ref/` so Rollup emits it
 * as a hashed asset instead of copying the whole reference folder.
 */
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  publicDir: false,
  server: { port: 5173, host: '127.0.0.1' },
  preview: { port: 4173, host: '127.0.0.1' },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2022',
    // The baked LOD tables are large base64 string literals; keep them out of
    // the inline-asset path and do not nag about the resulting chunk size.
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 8192,
    sourcemap: false,
  },
});
