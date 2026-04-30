/**
 * MapWebView.tsx
 * Leaflet.js map with Geoapify tiles — inside a WebView.
 *
 * FIXES applied:
 *  1. preferCanvas:true → Canvas renderer for polylines/circles
 *     → Eliminates "route shifts on zoom/pan" bug in Android WebView
 *  2. invalidateSize() on load/resize → fixes element displacement
 *  3. Destination red circleMarker added when setRoute() is called
 *  4. Simplified marker HTML (fewer DOM nodes) → less lag
 *  5. Marker limit = 15 max → less rendering overhead
 */

import React, { forwardRef, useImperativeHandle, useRef } from "react";
import { StyleSheet } from "react-native";
import WebView, { WebViewMessageEvent } from "react-native-webview";
import { GEOAPIFY_API_KEY } from "../../constants/config";
import { NearbyPlace } from "../../services/mapService";

const GEOAPIFY_KEY = GEOAPIFY_API_KEY;
const DEFAULT_LAT = 21.0285;
const DEFAULT_LNG = 105.8542;

export interface MapWebViewHandle {
  setUserLocation(lat: number, lng: number): void;
  setPlaces(places: NearbyPlace[], activeId: string | null): void;
  setRoute(coords: number[][]): void;
  clearRoute(): void;
  flyTo(lat: number, lng: number, zoom?: number): void;
  fitBounds(coords: number[][]): void;
}

interface Props {
  onMarkerPress: (placeId: string) => void;
  onMapPress: () => void;
}

const MapWebView = forwardRef<MapWebViewHandle, Props>(
  function MapWebView({ onMarkerPress, onMapPress }, ref) {
    const webViewRef = useRef<WebView>(null);
    const isReady = useRef(false);
    const queue = useRef<string[]>([]);

    const inject = (code: string) => {
      const js = `(function(){try{${code}}catch(e){console.warn('[Map]',String(e));}})();true;`;
      if (isReady.current) {
        webViewRef.current?.injectJavaScript(js);
      } else {
        queue.current.push(js);
      }
    };

    const handleLoadEnd = () => {
      isReady.current = true;
      const pending = [...queue.current];
      queue.current = [];
      pending.forEach((js) => webViewRef.current?.injectJavaScript(js));
    };

    const handleMessage = (e: WebViewMessageEvent) => {
      try {
        const msg = JSON.parse(e.nativeEvent.data);
        if (msg.type === "markerPress") onMarkerPress(msg.placeId);
        else if (msg.type === "mapPress") onMapPress();
      } catch {}
    };

    useImperativeHandle(ref, () => ({
      setUserLocation(lat, lng) {
        inject(`window._map.setUserLoc(${lat},${lng});`);
      },
      setPlaces(places, activeId) {
        inject(
          `window._map.setPlaces(${JSON.stringify(places)},${JSON.stringify(activeId)});`
        );
      },
      setRoute(coords) {
        inject(`window._map.setRoute(${JSON.stringify(coords)});`);
      },
      clearRoute() {
        inject(`window._map.clearRoute();`);
      },
      flyTo(lat, lng, zoom = 15) {
        inject(`window._map.leaflet.flyTo([${lat},${lng}],${zoom},{animate:true,duration:0.8});`);
      },
      fitBounds(coords) {
        inject(
          `window._map.leaflet.fitBounds(${JSON.stringify(coords)},{padding:[80,40],maxZoom:16});`
        );
      },
    }));

    return (
      <WebView
        ref={webViewRef}
        style={StyleSheet.absoluteFillObject}
        source={{ html: MAP_HTML }}
        onLoadEnd={handleLoadEnd}
        onMessage={handleMessage}
        scrollEnabled={false}
        bounces={false}
        originWhitelist={["*"]}
        javaScriptEnabled
        domStorageEnabled
        allowsInlineMediaPlayback
        mixedContentMode="always"
        androidLayerType="software"
        accessibilityLabel="Bản đồ cơ sở y tế"
      />
    );
  }
);

export default MapWebView;

// ─────────────────────────────────────────────────────────────────────────────
// MAP HTML
// FIX 1: preferCanvas:true  → Canvas renderer → route does NOT shift on zoom
// FIX 2: invalidateSize()   → Forces Leaflet to recalc size after WebView load
// FIX 3: Red circleMarker   → Destination pin when route is drawn
// FIX 4: Simplified markers → Fewer DOM nodes → less lag
// ─────────────────────────────────────────────────────────────────────────────
const MAP_HTML = `<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body,#map{width:100%;height:100%;overflow:hidden;background:#f0f4f8}
  .leaflet-control-zoom{display:none!important}
  .leaflet-control-attribution{font-size:8px;opacity:.45;background:rgba(255,255,255,.6)!important}
  @keyframes udpulse{
    0%  {box-shadow:0 0 0 0   rgba(61,191,160,.5)}
    70% {box-shadow:0 0 0 8px rgba(61,191,160,0)}
    100%{box-shadow:0 0 0 0   rgba(61,191,160,0)}
  }
  .u-dot{width:14px;height:14px;border-radius:50%;background:#3DBFA0;border:2.5px solid #fff;animation:udpulse 2s infinite}
</style>
</head>
<body>
<div id="map"></div>
<script>
(function(){
  var KEY='${GEOAPIFY_KEY}';

  // ── Init Leaflet map ──────────────────────────────────────────────
  // preferCanvas: true = Canvas renderer for ALL vector elements
  // WHY: In Android WebView, SVG elements can shift/misalign during
  // zoom because SVG uses CSS transforms while tiles use pixel offsets.
  // Canvas redraws everything from scratch each frame → no misalignment.
  var leaf = L.map('map',{
    zoomControl:         false,
    tap:                 false,
    tapTolerance:        10,
    preferCanvas:        true,         // KEY: canvas renderer
    markerZoomAnimation: false         // skip for performance
  }).setView([${DEFAULT_LAT},${DEFAULT_LNG}],14);

  window._map = { leaflet: leaf };

  // ── Tiles ─────────────────────────────────────────────────────────
  L.tileLayer(
    'https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png?apiKey='+KEY,
    {
      attribution: '\u0026copy; <a href="https://geoapify.com">Geoapify</a> \u0026copy; <a href="https://openstreetmap.org/copyright">OSM</a>',
      maxZoom:      20,
      detectRetina: false,
      updateWhenIdle: true,
      keepBuffer:   2
    }
  ).addTo(leaf);

  // ── FIX: invalidateSize prevents element displacement in WebView ──
  // Android WebView doesn't always fire resize. Call this to force
  // Leaflet to recalculate container dims → route/markers align correctly.
  function _fixSize(){ leaf.invalidateSize(false); }
  setTimeout(_fixSize,  80);
  setTimeout(_fixSize, 400);
  window.addEventListener('resize', _fixSize);
  leaf.on('zoomend', function(){ setTimeout(_fixSize, 60); });

  var userMk=null, placeMks=[], routeLy=null, destMk=null;

  // ── Map tap (suppressed after drag) ──────────────────────────────
  var _dragging=false;
  leaf.on('dragstart',function(){ _dragging=true; });
  leaf.on('dragend',  function(){ setTimeout(function(){ _dragging=false; },150); });
  leaf.on('click',    function(){ if(!_dragging) _post({type:'mapPress'}); });

  function _post(obj){
    try{ window.ReactNativeWebView.postMessage(JSON.stringify(obj)); }catch(e){}
  }

  // ── Marker icon (simplified HTML = less DOM = faster) ────────────
  function _mkIcon(name,isAct){
    var bg  = isAct ? '#3DBFA0' : '#5B6A80';
    var lbl = name.length>14 ? name.substring(0,12)+'..' : name;
    var sh  = isAct ? 'box-shadow:0 3px 10px rgba(61,191,160,.5);' : '';
    var sc  = isAct ? 'transform:scale(1.08);' : '';
    var html=
      '<div style="display:inline-flex;flex-direction:column;align-items:center">'+
        '<div style="width:28px;height:28px;border-radius:8px;background:'+bg+
             ';border:2px solid #fff;display:flex;align-items:center;justify-content:center;'+sh+sc+'">'+
          '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round">'+
            '<path d="M12 5v14M5 12h14"/>'+
          '</svg>'+
        '</div>'+
        '<div style="width:0;height:0;border-left:4px solid transparent;border-right:4px solid transparent;border-top:5px solid '+bg+';margin-top:-1px"></div>'+
        '<div style="font-size:9px;font-weight:700;color:#fff;background:'+bg+
             ';border-radius:3px;padding:1px 4px;margin-top:2px;max-width:84px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+lbl+'</div>'+
      '</div>';
    return L.divIcon({html:html,className:'',iconSize:[28,48],iconAnchor:[14,33]});
  }

  // ── API: User GPS dot ─────────────────────────────────────────────
  window._map.setUserLoc=function(lat,lng){
    if(userMk){ userMk.setLatLng([lat,lng]); return; }
    userMk=L.marker([lat,lng],{
      icon:L.divIcon({html:'<div class="u-dot"></div>',className:'',iconSize:[14,14],iconAnchor:[7,7]}),
      zIndexOffset:1000,
      interactive:false
    }).addTo(leaf);
  };

  // ── API: Place markers (max 15 for performance) ───────────────────
  window._map.setPlaces=function(places,activeId){
    placeMks.forEach(function(m){ leaf.removeLayer(m); });
    placeMks=[];
    var visible=places.slice(0,15); // limit to 15
    visible.forEach(function(p){
      var isAct=(p.place_id===activeId);
      var mk=L.marker([p.latitude,p.longitude],{
        icon:_mkIcon(p.name,isAct),
        zIndexOffset:isAct?500:0
      }).addTo(leaf);
      mk.on('click',function(e){
        L.DomEvent.stopPropagation(e);
        _post({type:'markerPress',placeId:p.place_id});
      });
      placeMks.push(mk);
    });
  };

  // ── API: Route polyline + red destination marker ──────────────────
  // circleMarker renders on CANVAS (no SVG overhead)
  // → Does NOT shift on zoom because canvas is redrawn per frame
  window._map.setRoute=function(coords){
    if(routeLy){ leaf.removeLayer(routeLy); routeLy=null; }
    if(destMk) { leaf.removeLayer(destMk);  destMk=null;  }
    if(!coords||!coords.length) return;

    // Route line
    routeLy=L.polyline(coords,{
      color:'#3DBFA0',weight:5,opacity:.9,
      lineCap:'round',lineJoin:'round'
    }).addTo(leaf);

    // Red destination pin (canvas circleMarker — no shifting)
    var last=coords[coords.length-1];
    destMk=L.circleMarker(last,{
      radius:10,
      color:'#fff',
      weight:3,
      fillColor:'#EF4444',
      fillOpacity:1
    }).addTo(leaf);
  };

  window._map.clearRoute=function(){
    if(routeLy){ leaf.removeLayer(routeLy); routeLy=null; }
    if(destMk) { leaf.removeLayer(destMk);  destMk=null;  }
  };

})();
</script>
</body>
</html>`;
