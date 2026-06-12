import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{r as c}from"./index-DzGJhHoF.js";import{c as u}from"./utils-DaT-yT0k.js";import{c as p}from"./createLucideIcon-C15OmZG9.js";import{B as x}from"./Button-BnaN5BD7.js";/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const f=p("X",[["path",{d:"M18 6 6 18",key:"1bl5f8"}],["path",{d:"m6 6 12 12",key:"d8bk6v"}]]),h={sm:"max-w-sm",md:"max-w-md",lg:"max-w-lg",xl:"max-w-2xl"};function n({isOpen:s,onClose:t,children:i,maxWidth:m="md",title:a}){return s?e.jsxs("div",{className:"fixed inset-0 z-50 flex items-center justify-center p-4",children:[e.jsx("div",{className:"absolute inset-0 bg-black/40 backdrop-blur-sm",onClick:t}),e.jsxs("div",{className:u("relative bg-card rounded-2xl border border-border shadow-2xl w-full animate-slide-in",h[m]),children:[a&&e.jsxs("div",{className:"flex items-center justify-between px-6 py-4 border-b border-border",children:[a&&e.jsx("h3",{className:"text-base font-semibold text-foreground",children:a}),e.jsx("button",{onClick:t,className:"ml-auto p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-all",children:e.jsx(f,{className:"w-4 h-4"})})]}),e.jsx("div",{className:"max-h-[75vh] overflow-y-auto",children:i})]})]}):null}n.__docgenInfo={description:"",methods:[],displayName:"Modal",props:{isOpen:{required:!0,tsType:{name:"boolean"},description:""},onClose:{required:!0,tsType:{name:"signature",type:"function",raw:"() => void",signature:{arguments:[],return:{name:"void"}}},description:""},children:{required:!0,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},maxWidth:{required:!1,tsType:{name:"union",raw:"'sm' | 'md' | 'lg' | 'xl'",elements:[{name:"literal",value:"'sm'"},{name:"literal",value:"'md'"},{name:"literal",value:"'lg'"},{name:"literal",value:"'xl'"}]},description:"",defaultValue:{value:"'md'",computed:!1}},title:{required:!1,tsType:{name:"string"},description:""}}};const N={title:"UI/Modal",component:n,tags:["autodocs"],argTypes:{maxWidth:{control:"select",options:["sm","md","lg","xl"]}}},r={render:()=>{const[s,t]=c.useState(!0);return e.jsxs(e.Fragment,{children:[e.jsx(x,{onClick:()=>t(!0),children:"打开弹窗"}),e.jsx(n,{isOpen:s,onClose:()=>t(!1),title:"示例弹窗",children:e.jsx("div",{className:"p-6",children:e.jsx("p",{className:"text-sm text-muted-foreground",children:"这是弹窗内容区域。"})})})]})}};var o,l,d;r.parameters={...r.parameters,docs:{...(o=r.parameters)==null?void 0:o.docs,source:{originalSource:`{
  render: () => {
    const [open, setOpen] = useState(true);
    return <>\r
        <Button onClick={() => setOpen(true)}>打开弹窗</Button>\r
        <Modal isOpen={open} onClose={() => setOpen(false)} title="示例弹窗">\r
          <div className="p-6">\r
            <p className="text-sm text-muted-foreground">这是弹窗内容区域。</p>\r
          </div>\r
        </Modal>\r
      </>;
  }
}`,...(d=(l=r.parameters)==null?void 0:l.docs)==null?void 0:d.source}}};const w=["Default"];export{r as Default,w as __namedExportsOrder,N as default};
