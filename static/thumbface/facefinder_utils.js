var facefinder_classify_region = function(r, c, s, pixels, ldim) {return -1.0;};
var cascadeurl = '/static/thumbface/facefinder.model';

fetch(cascadeurl).then(function(response) {
  response.arrayBuffer().then(function(buffer) {
    var bytes = new Int8Array(buffer);
    facefinder_classify_region = pico.unpack_cascade(bytes);
    console.log('Pico facescanner model loaded');
  });
});

function rgba_to_grayscale(rgba, nrows, ncols) {
  var gray = new Uint8Array(nrows*ncols);
  for(var r=0; r<nrows; ++r)
    for(var c=0; c<ncols; ++c)
      // gray = 0.2*red + 0.7*green + 0.1*blue
      gray[r*ncols + c] = (2*rgba[r*4*ncols+4*c+0]+7*rgba[r*4*ncols+4*c+1]+1*rgba[r*4*ncols+4*c+2])/10;
  return gray;
}

function blobToDataURI(b) {
  return new Promise(function(resolve, reject) {
    const reader = new FileReader();

    reader.onloadend = function() {
      resolve(reader.result);
    };

    reader.readAsDataURL(b);
  });
}

async function URLToDataURI(url) {
  try {
    const response = await fetch(url);
    const blob = await response.blob();
    return await blobToDataURI(blob);
  } catch {
    return false;
  }
}

async function createImageObject(uri) {
  return new Promise((resolve, reject) => {
    let img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = uri;
  });
}

async function getFaceCount(url) {
  let dataURI = await URLToDataURI(url);

  if (!dataURI) {
      // likely a fetch error
      return 0;
  }

  let canvas = document.createElement('canvas');
  canvas.width = 440;
  canvas.height = 248;
  let ctx = canvas.getContext('2d');

  let img = await createImageObject(dataURI);
  ctx.drawImage(img, 0, 0);

  var rgba = ctx.getImageData(0, 0, 480, 360).data;
  // prepare input to `run_cascade`
  image = {
    "pixels": rgba_to_grayscale(rgba, 360, 480),
    "nrows": 360,
    "ncols": 480,
    "ldim": 480
  };

  params = {
    "shiftfactor": 0.1, // move the detection window by 10% of its size
    "minsize": 20,      // minimum size of a face (not suitable for real-time detection, set it to 100 in that case)
    "maxsize": 1000,    // maximum size of a face
    "scalefactor": 1.1  // for multiscale processing: resize the detection window by 10% when moving to the higher scale
  };

  // run the cascade over the image
  // dets is an array that contains (r, c, s, q) quadruplets
  // (representing row, column, scale and detection score)
  dets = pico.run_cascade(image, facefinder_classify_region, params);
  // cluster the obtained detections
  dets = pico.cluster_detections(dets, 0.2); // set IoU threshold to 0.2
  // draw results
  qthresh = 5.0 // this constant is empirical: other cascades might require a different one

  let faceCount = 0;
  for (i=0; i < dets.length; ++i) {
    // check the detection score
    // if it's above the threshold, draw it
    if (dets[i][3] > qthresh) {
      faceCount++;
      // ctx.beginPath();
      // ctx.arc(dets[i][1], dets[i][0], dets[i][2]/2, 0, 2*Math.PI, false);
      // ctx.lineWidth = 3;
      // ctx.strokeStyle = 'red';
      // ctx.stroke();
    }
  }
  return faceCount;
}
