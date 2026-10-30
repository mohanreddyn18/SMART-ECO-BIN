import * as ort from 'onnxruntime-web/wasm';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const modelPath = resolve('public/models/waste_classifier.onnx');
const model = await readFile(modelPath);
ort.env.wasm.numThreads = 1;
ort.env.wasm.wasmBinary = await readFile(resolve('node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.wasm'));
const session = await ort.InferenceSession.create(model, { executionProviders: ['wasm'] });
const input = new ort.Tensor('float32', new Float32Array(3 * 224 * 224), [1, 3, 224, 224]);
const results = await session.run({ [session.inputNames[0]]: input });
const output = results[session.outputNames[0]];
const expectedLogits = [
  -1.1128311, -0.0086674, -2.0320261, 2.4446657, -0.1274069, -0.8164204,
  -1.6213256, 1.3561177, -0.7646435, -1.4016345, -1.3355082, -1.9069245
];
if (output.data.length !== expectedLogits.length || [...output.data].some((value, index) => (
  !Number.isFinite(value) || Math.abs(value - expectedLogits[index]) > 0.001
))) {
  throw new Error(`ONNX output did not match PyTorch fixture: ${JSON.stringify([...output.data])}`);
}
console.log(`ONNX Runtime Web CPU inference matches the PyTorch export fixture: ${output.data.length} logits within 1e-3.`);
