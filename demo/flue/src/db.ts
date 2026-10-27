// Conversations hold prompts and model output; keep them in process memory only.
// `flue run` would otherwise persist them in node_modules/.cache/flue/run.db.
import { sqlite } from '@flue/runtime/node';

export default sqlite(':memory:');
