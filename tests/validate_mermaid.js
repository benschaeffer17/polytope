const { JSDOM } = require('jsdom');
const fs = require('fs');

const dom = new JSDOM('');
global.window = dom.window;
global.document = dom.window.document;

// Properly instantiate DOMPurify
const createDOMPurify = require('dompurify');
global.DOMPurify = createDOMPurify(global.window);

const diagram = fs.readFileSync(0, 'utf-8');

async function validate() {
    // Dynamically import the ES module 'mermaid'
    const { default: mermaid } = await import('mermaid');
    
    mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });

    try {
        await mermaid.parse(diagram);
        process.exit(0);
    } catch (error) {
        console.error("Mermaid Syntax Error:");
        console.error(error.message || error);
        process.exit(1);
    }
}

validate();
