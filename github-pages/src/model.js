import * as ort from 'onnxruntime-web/wasm';

const classNames = [
  'battery', 'biological', 'brown-glass', 'cardboard', 'clothes',
  'green-glass', 'metal', 'paper', 'plastic', 'shoes', 'trash', 'white-glass'
];

const routes = {
  battery: ['Hazardous / e-waste', 'Battery drop-off', 'Keep separate from household waste. Take batteries to an approved collection point.'],
  biological: ['Organic / wet waste', 'Organic compost', 'Place food and biodegradable matter in the local organics stream. Remove non-compostable packaging.'],
  'brown-glass': ['Recyclable / glass', 'Glass recycling', 'Empty and rinse. Keep glass separate where your local service requests color sorting.'],
  cardboard: ['Recyclable / dry waste', 'Paper and cardboard recycling', 'Keep dry, remove food contamination, and flatten before recycling.'],
  clothes: ['Reusable / textile', 'Textile collection', 'Donate wearable items or use a textile collection point. Check local acceptance first.'],
  'green-glass': ['Recyclable / glass', 'Glass recycling', 'Empty and rinse. Keep glass separate where your local service requests color sorting.'],
  metal: ['Recyclable / dry waste', 'Metal recycling', 'Empty and rinse containers. Follow local rules for sharp or pressurized items.'],
  paper: ['Recyclable / dry waste', 'Paper recycling', 'Keep clean and dry. Greasy or food-soiled paper may belong in residual waste.'],
  plastic: ['Recyclable / dry waste', 'Plastic recycling', 'Empty and rinse. Check local guidance because accepted plastic types vary.'],
  shoes: ['Reusable / textile', 'Footwear collection', 'Donate wearable footwear or use a local textile collection service.'],
  trash: ['Residual / manual review', 'General residual waste', 'Check local disposal guidance. Separate hazardous components before disposal.'],
  'white-glass': ['Recyclable / glass', 'Glass recycling', 'Empty and rinse. Keep glass separate where your local service requests color sorting.']
};

let sessionPromise;

async function getSession() {
  if (!sessionPromise) {
    sessionPromise = (async () => {
      ort.env.wasm.numThreads = 1;
      const modelUrl = new URL(`${import.meta.env.BASE_URL}models/waste_classifier.onnx`, window.location.href).href;
      return ort.InferenceSession.create(modelUrl, {
        executionProviders: ['wasm'],
        graphOptimizationLevel: 'all'
      });
    })().catch((error) => {
      sessionPromise = undefined;
      throw error;
    });
  }
  return sessionPromise;
}

async function imageToTensor(file) {
  const bitmap = await createImageBitmap(file);
  try {
    const canvas = document.createElement('canvas');
    canvas.width = 224;
    canvas.height = 224;
    const context = canvas.getContext('2d', { willReadFrequently: true });
    if (!context) throw new Error('This browser could not prepare the image for inference.');
    context.drawImage(bitmap, 0, 0, 224, 224);
    const { data } = context.getImageData(0, 0, 224, 224);
    const input = new Float32Array(1 * 3 * 224 * 224);
    const mean = [0.485, 0.456, 0.406];
    const std = [0.229, 0.224, 0.225];
    for (let pixel = 0; pixel < 224 * 224; pixel += 1) {
      for (let channel = 0; channel < 3; channel += 1) {
        input[channel * 224 * 224 + pixel] = (data[pixel * 4 + channel] / 255 - mean[channel]) / std[channel];
      }
    }
    return new ort.Tensor('float32', input, [1, 3, 224, 224]);
  } finally {
    bitmap.close();
  }
}

export async function classifyImage(file) {
  const session = await getSession();
  const inputTensor = await imageToTensor(file);
  const results = await session.run({ [session.inputNames[0]]: inputTensor });
  const output = results[session.outputNames[0]].data;
  if (output.length !== classNames.length) {
    throw new Error(`Unexpected model output: expected ${classNames.length} scores, received ${output.length}.`);
  }
  const maxLogit = Math.max(...output);
  const exp = Array.from(output, (value) => Math.exp(value - maxLogit));
  const sum = exp.reduce((total, value) => total + value, 0);
  let bestIndex = 0;
  for (let index = 1; index < exp.length; index += 1) {
    if (exp[index] > exp[bestIndex]) bestIndex = index;
  }
  const predictedClass = classNames[bestIndex];
  const confidence = (exp[bestIndex] / sum) * 100;
  const [category, disposalBin, recommendation] = routes[predictedClass];
  const requiresManualReview = confidence < 60;
  return {
    predictedClass,
    confidence: Math.round(confidence * 100) / 100,
    category: requiresManualReview ? 'Uncertain / manual review' : category,
    disposalBin: requiresManualReview ? 'Manual review' : disposalBin,
    recommendation: requiresManualReview
      ? 'The model confidence is low. Inspect this item and follow local waste authority guidance.'
      : recommendation,
    requiresManualReview,
    model: 'MobileNetV2 12-class classifier (ONNX Runtime Web)',
    inference: 'Executed locally in this browser'
  };
}

export { classNames };
