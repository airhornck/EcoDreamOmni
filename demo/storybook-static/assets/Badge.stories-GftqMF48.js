import{j as a}from"./jsx-runtime-D_zvdyIk.js";import{B as r}from"./Badge-kMiPxsto.js";import"./utils-DaT-yT0k.js";const A={title:"UI/Badge",component:r,tags:["autodocs"],argTypes:{variant:{control:"select",options:["default","primary","success","warning","danger","info"]}}},e={args:{children:"草稿",variant:"default"}},n={args:{children:"已通过",variant:"success"}},s={args:{children:"审核中",variant:"warning"}},c={args:{children:"已驳回",variant:"danger"}},i={render:()=>a.jsxs("div",{className:"flex flex-wrap gap-2",children:[a.jsx(r,{variant:"default",children:"default"}),a.jsx(r,{variant:"primary",children:"primary"}),a.jsx(r,{variant:"success",children:"success"}),a.jsx(r,{variant:"warning",children:"warning"}),a.jsx(r,{variant:"danger",children:"danger"}),a.jsx(r,{variant:"info",children:"info"})]})};var t,d,o;e.parameters={...e.parameters,docs:{...(t=e.parameters)==null?void 0:t.docs,source:{originalSource:`{
  args: {
    children: '草稿',
    variant: 'default'
  }
}`,...(o=(d=e.parameters)==null?void 0:d.docs)==null?void 0:o.source}}};var g,l,p;n.parameters={...n.parameters,docs:{...(g=n.parameters)==null?void 0:g.docs,source:{originalSource:`{
  args: {
    children: '已通过',
    variant: 'success'
  }
}`,...(p=(l=n.parameters)==null?void 0:l.docs)==null?void 0:p.source}}};var m,u,v;s.parameters={...s.parameters,docs:{...(m=s.parameters)==null?void 0:m.docs,source:{originalSource:`{
  args: {
    children: '审核中',
    variant: 'warning'
  }
}`,...(v=(u=s.parameters)==null?void 0:u.docs)==null?void 0:v.source}}};var f,h,x;c.parameters={...c.parameters,docs:{...(f=c.parameters)==null?void 0:f.docs,source:{originalSource:`{
  args: {
    children: '已驳回',
    variant: 'danger'
  }
}`,...(x=(h=c.parameters)==null?void 0:h.docs)==null?void 0:x.source}}};var B,j,w;i.parameters={...i.parameters,docs:{...(B=i.parameters)==null?void 0:B.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">\r
      <Badge variant="default">default</Badge>\r
      <Badge variant="primary">primary</Badge>\r
      <Badge variant="success">success</Badge>\r
      <Badge variant="warning">warning</Badge>\r
      <Badge variant="danger">danger</Badge>\r
      <Badge variant="info">info</Badge>\r
    </div>
}`,...(w=(j=i.parameters)==null?void 0:j.docs)==null?void 0:w.source}}};const E=["Default","Success","Warning","Danger","AllVariants"];export{i as AllVariants,c as Danger,e as Default,n as Success,s as Warning,E as __namedExportsOrder,A as default};
