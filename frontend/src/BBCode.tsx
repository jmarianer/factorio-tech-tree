import BBCodeComponent from '@bbob/react';
import { createPreset } from '@bbob/preset';

const factorioPreset = createPreset({
  font: (node) => (
     {
      tag: 'b',
      content: node.content,
    }),
  color: (node) => ({
      tag: 'span',
      attrs: {
        style: {
          color: Object.keys(node.attrs || {})[0],
        },
      },
      content: node.content,
    }),
  br: () => ({ tag: 'br' }),
  // TODO fix img
  img: () => ({ tag: 'i' }),
})

export function BBCode(props: { code: string }) {
  return <BBCodeComponent plugins={[factorioPreset()]}>{props.code.replaceAll('\\n', '[br]')}</BBCodeComponent>;
}
