# Fabric.js 7.x performance notes

Validated against Fabric.js official docs/repository on 2026-10-03.

## Current version
Fabric.js 7.4.0 is the latest release and includes security fixes plus viewport rotation fixes.
https://github.com/fabricjs/fabric.js/releases

## Caching
Official caching guide:
https://www.fabricjs.com/docs/fabric-object-caching/

Key observations:
- objectCaching draws an object into an offscreen cache and reuses it during transforms;
- `noScaleCache=true` avoids regenerating cache continuously while scaling and refreshes after interaction;
- caching has memory/quality tradeoffs and can be slower for many simple objects;
- viewport zoom invalidates/resizes many caches and can become a performance hotspot;
- global cache limits exist, but must not be raised blindly.

Project consequence:
- favor photo-in-slot transforms over global viewport zoom;
- keep object graph small;
- change Fabric cache configuration only after profiling the actual 18-slot case.
