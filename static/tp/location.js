if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const latitude = position.coords.latitude;
      const longitude = position.coords.longitude;
      const geolocationHeader = `${latitude},${longitude}`;

      // Make the request to your Django view
      fetch('/your-view-url/', {
        method: 'POST', 
        headers: {
          'geolocation': geolocationHeader,
          'allow_location': 'true', 
          // Include other necessary headers
        },
        // ... (rest of the fetch request) ...
      })
      .then(response => { 
        // Handle the response from the server
      })
      .catch(error => {
        console.error('Error:', error);
      });
    },
    (error) => {
      console.error('Error obtaining location:', error);
    }
  );
} else {
  console.log('Geolocation is not supported by this browser.');
}