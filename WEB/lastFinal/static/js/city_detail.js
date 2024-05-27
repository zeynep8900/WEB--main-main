mapboxgl.accessToken = 'pk.eyJ1Ijoic2V6YWkzNSIsImEiOiJjbHdub3Q2cjAxdW5wMmpteTdtZ2htcDVwIn0.Tt6d8m6LRzkeavcYQ_AGYw';

function initMap() {
  const cityLat = parseFloat('{{ city.latitude }}');
  const cityLng = parseFloat('{{ city.longitude }}');

  mapboxgl.accessToken = 'pk.eyJ1Ijoic2V6YWkzNSIsImEiOiJjbHdub3Q2cjAxdW5wMmpteTdtZ2htcDVwIn0.Tt6d8m6LRzkeavcYQ_AGYw';

  const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [cityLng, cityLat],
    zoom: 12
  });

  new mapboxgl.Marker()
    .setLngLat([cityLng, cityLat])
    .setPopup(new mapboxgl.Popup({ offset: 25 }).setText('{{ city.city_name }}'))
    .addTo(map);

  document.getElementById('showRouteButton').addEventListener('click', function() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(function(position) {
        const yourLat = position.coords.latitude;
        const yourLng = position.coords.longitude;

        const directionsRequest = `https://api.mapbox.com/directions/v5/mapbox/driving/${yourLng},${yourLat};${cityLng},${cityLat}?access_token=${mapboxgl.accessToken}`;
        fetch(directionsRequest)
          .then(response => response.json())
          .then(data => {
            const route = data.routes[0].geometry.coordinates;
            const geojson = {
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'LineString',
                coordinates: route
              }
            };

            if (map.getSource('route')) {
              map.getSource('route').setData(geojson);
            } else {
              map.addLayer({
                id: 'route',
                type: 'line',
                source: {
                  type: 'geojson',
                  data: geojson
                },
                layout: {
                  'line-join': 'round',
                  'line-cap': 'round'
                },
                paint: {
                  'line-color': '#888',
                  'line-width': 8
                }
              });
            }
          });
      });
    } else {
      window.alert('Your browser does not support geolocation.');
    }
  });
}

document.addEventListener('DOMContentLoaded', initMap); // Sayfa yüklendiğinde haritayı başlat
