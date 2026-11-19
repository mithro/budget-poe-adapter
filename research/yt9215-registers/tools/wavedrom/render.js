// Render WaveDrom sources as SVG.
//
// Reads one JSON source per line on standard input and writes one line per
// source on standard output: a JSON object with "svg", or with "error".
'use strict';

const readline = require('readline');
const wavedrom = require('wavedrom');
const onml = require('onml');

let index = 0;

readline.createInterface({input: process.stdin}).on('line', line => {
    let out;
    try {
        const tree = wavedrom.renderAny(index++, JSON.parse(line), wavedrom.waveSkin);
        if (tree[0] !== 'svg') {
            throw new Error('the source has neither "signal" nor "reg"');
        }
        out = {svg: onml.stringify(tree)};
    } catch (err) {
        out = {error: String(err && err.message || err)};
    }
    process.stdout.write(JSON.stringify(out) + '\n');
});
