# Vendored: three.js

Pinned so the published site makes **zero external requests at runtime**. Nothing
here is fetched from a CDN; everything the viewer needs is in this directory.

| field | value |
|---|---|
| package | `three` |
| version | **0.185.1** (r185.1) |
| source | `https://registry.npmjs.org/three/-/three-0.185.1.tgz` |
| tarball sha256 | `a2143f5bf978bd3470a51024b2b6bdd581913ba8f36ff1538d433f3a95adf2df` |
| tarball sha1 (matches registry `dist.shasum`) | `63e9e241a17b101e211965121a017b4b4d8054ae` |
| registry integrity | `sha512-5aojFCXKwnjBRZvUnt3WFfEcvUJgkN5LlijRFN95hMy8WVkG4I0QNcJE+OuWvuJ0bOdStrbfXn0pkd6/QyiAlg==` |
| retrieved | 2026-08-20 |
| license | MIT (`LICENSE`, copied verbatim from the package) |

## Files taken from the tarball

| vendored path | tarball path | sha256 |
|---|---|---|
| `three.module.min.js` | `package/build/three.module.min.js` | `86bcee248b64f44bcfc23c331ae74619061957d59cab040171dcb6fb5900beb6` |
| `three.core.min.js` | `package/build/three.core.min.js` | `05b2609338c76cd65daf74f3ac515bc9a5045e1b3b33edc07d8c9bd55250fa90` |
| `addons/loaders/GLTFLoader.js` | `package/examples/jsm/loaders/GLTFLoader.js` | `97642d720f16cc9a0c9844934198e4d0c023bea8e89576d0f7545d03b2d103d2` |
| `addons/controls/OrbitControls.js` | `package/examples/jsm/controls/OrbitControls.js` | `faabb4e8dfd9235ee4a9fd7c9a3d75f90f1689dbd4944bd6fd32117dacec5f93` |
| `addons/utils/BufferGeometryUtils.js` | `package/examples/jsm/utils/BufferGeometryUtils.js` | `5c552223a9309883743b80538d6e9cdb45e3227f30d3ec56fb2c39b46e78d595` |
| `addons/utils/SkeletonUtils.js` | `package/examples/jsm/utils/SkeletonUtils.js` | `b1632a703206c3d830de9fcbe515696770d04b71a15ee6b50afa6d2c3298c86f` |
| `addons/environments/RoomEnvironment.js` | `package/examples/jsm/environments/RoomEnvironment.js` | `55f466192cc84298755a424c5e040345006b2ee1455589b3b54126c2ea4123f4` |
| `addons/postprocessing/EffectComposer.js` | `package/examples/jsm/postprocessing/EffectComposer.js` | `4e079a5886152d7e529a59aef644e968ab4d32c6a33ce016b36bf29b2eac26f7` |
| `addons/postprocessing/Pass.js` | `package/examples/jsm/postprocessing/Pass.js` | `444b409c235ead986893c472e720da1b779a56985c7d10b279c7944b52bd61c5` |
| `addons/postprocessing/RenderPass.js` | `package/examples/jsm/postprocessing/RenderPass.js` | `817f6c3cdcd0fd41515d112359ea0532568eefb5aabd3b33903957ebca1b8a6a` |
| `addons/postprocessing/ShaderPass.js` | `package/examples/jsm/postprocessing/ShaderPass.js` | `e2500a5913b26bbf5148ceaae644c6edcff06a18b01494ee37bf856353d2ab9d` |
| `addons/postprocessing/MaskPass.js` | `package/examples/jsm/postprocessing/MaskPass.js` | `7cd08eee9d5d6f5578beaddbdcbe9c384f6873810af27f22ab7db3ceeb127aa3` |
| `addons/postprocessing/UnrealBloomPass.js` | `package/examples/jsm/postprocessing/UnrealBloomPass.js` | `1158bb02f6467889aba19c1a788b9107054d7f6a558498b5e2152db5873bb859` |
| `addons/postprocessing/OutputPass.js` | `package/examples/jsm/postprocessing/OutputPass.js` | `02e4a261af34de71338185e9e87f0cbe5cba9115608d984363e1269dec1d2272` |
| `addons/shaders/CopyShader.js` | `package/examples/jsm/shaders/CopyShader.js` | `a33057d5ac91c43304c186ac0e8816e62bb2ed471d3a00ff3018dfd5c0389718` |
| `addons/shaders/LuminosityHighPassShader.js` | `package/examples/jsm/shaders/LuminosityHighPassShader.js` | `5044f780b6e6cf863947f64c36fe1587132f7fbe395ada863cd1e5f0388dcf1e` |
| `addons/shaders/OutputShader.js` | `package/examples/jsm/shaders/OutputShader.js` | `353479f77a8d7e2629d49ccac9fc2f5dbfdda5442e0adf867b00377a2fcb0cb2` |
| `LICENSE` | `package/LICENSE` | `8b378ebe60e2fe500158cb0ac71cb5e8b7d92953c2abcc63a0eb90499653b5bc` |

`SkeletonUtils.js` and `BufferGeometryUtils.js` are here because `GLTFLoader.js`
imports them (`clone`, `toTrianglesDrawMode`); nothing else pulls them in.
`RoomEnvironment.js` is a procedurally built studio env map — it is what lights
the matte and transmissive materials, and it means the page ships no .hdr file
and fetches nothing.
`three.module.min.js` imports `./three.core.min.js` — keep the two side by side.

## The postprocessing set, and why the LED band needs it

Round 4: "It's just a hard band which is ridiculous. Should really look like a
diffuse glow." A self-lit mesh cannot look like light — a screen pixel stops at
white — so the render needs **bloom**, and bloom is a post pass. `viewer.js`
therefore composes `RenderPass -> UnrealBloomPass -> OutputPass` whenever the
lighting is switched on, and calls `renderer.render()` directly when it is off,
so nothing is paid for on an unlit render.

The seven postprocessing files and three shaders above are the exact import
closure of that chain, from the SAME tarball as everything else:

```
EffectComposer -> CopyShader, ShaderPass, MaskPass
RenderPass, ShaderPass, MaskPass, UnrealBloomPass, OutputPass -> Pass
UnrealBloomPass -> CopyShader, LuminosityHighPassShader
OutputPass -> OutputShader
```

`OutputPass` is mandatory, not decorative: three.js applies tone mapping and the
sRGB transfer only when it renders to the CANVAS, so a composer chain hands the
bloom pass raw linear HDR (the composer's own buffer is `HalfFloatType`) and
`OutputPass` puts the tone curve back at the end. That is what lets the emissive
ribbon carry values well above 1.0 and be the only thing the bloom threshold
catches, leaving the device itself crisp.

## How the site resolves it

`index.html` carries an import map:

```json
{ "imports": { "three": "./vendor/three/three.module.min.js",
               "three/addons/": "./vendor/three/addons/" } }
```

so `viewer.js` uses the same specifiers three's own docs use, with no bundler
and no network.

## Re-verify

```sh
curl -sSL -o three-0.185.1.tgz https://registry.npmjs.org/three/-/three-0.185.1.tgz
shasum -a 256 three-0.185.1.tgz     # must equal the tarball sha256 above
cd configurator/site/vendor/three && shasum -a 256 \
  LICENSE addons/controls/OrbitControls.js addons/loaders/GLTFLoader.js \
  addons/utils/BufferGeometryUtils.js addons/utils/SkeletonUtils.js \
  addons/environments/RoomEnvironment.js \
  addons/postprocessing/EffectComposer.js addons/postprocessing/Pass.js \
  addons/postprocessing/RenderPass.js addons/postprocessing/ShaderPass.js \
  addons/postprocessing/MaskPass.js addons/postprocessing/UnrealBloomPass.js \
  addons/postprocessing/OutputPass.js \
  addons/shaders/CopyShader.js addons/shaders/LuminosityHighPassShader.js \
  addons/shaders/OutputShader.js \
  three.core.min.js three.module.min.js
```

## Upgrading

Replace all eighteen files from one tarball at one version, rewrite both tables,
and re-run `configurator/tests/site_selfcontained.test.mjs` — it walks the
served tree and fails on any absolute `http(s)://` reference.
