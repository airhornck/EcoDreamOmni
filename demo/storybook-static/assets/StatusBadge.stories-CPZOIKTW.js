import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{B as I}from"./Badge-kMiPxsto.js";import"./utils-DaT-yT0k.js";const N={draft:{text:"草稿",variant:"default"},reviewing:{text:"审核中",variant:"warning"},approved:{text:"已通过",variant:"success"},published:{text:"已发布",variant:"info"},rejected:{text:"已驳回",variant:"danger"}};function s({status:_}){const u=N[_];return e.jsx(I,{variant:u.variant,children:u.text})}s.__docgenInfo={description:"",methods:[],displayName:"StatusBadge",props:{status:{required:!0,tsType:{name:"ContentItem['status']",raw:"ContentItem['status']"},description:""}}};const P={title:"Common/StatusBadge",component:s,tags:["autodocs"]},t={args:{status:"draft"}},a={args:{status:"reviewing"}},r={args:{status:"approved"}},n={args:{status:"published"}},o={args:{status:"rejected"}},d={render:()=>e.jsxs("div",{className:"flex flex-wrap gap-2",children:[e.jsx(s,{status:"draft"}),e.jsx(s,{status:"reviewing"}),e.jsx(s,{status:"approved"}),e.jsx(s,{status:"published"}),e.jsx(s,{status:"rejected"})]})};var c,i,p;t.parameters={...t.parameters,docs:{...(c=t.parameters)==null?void 0:c.docs,source:{originalSource:`{
  args: {
    status: 'draft'
  }
}`,...(p=(i=t.parameters)==null?void 0:i.docs)==null?void 0:p.source}}};var m,g,l;a.parameters={...a.parameters,docs:{...(m=a.parameters)==null?void 0:m.docs,source:{originalSource:`{
  args: {
    status: 'reviewing'
  }
}`,...(l=(g=a.parameters)==null?void 0:g.docs)==null?void 0:l.source}}};var v,x,f;r.parameters={...r.parameters,docs:{...(v=r.parameters)==null?void 0:v.docs,source:{originalSource:`{
  args: {
    status: 'approved'
  }
}`,...(f=(x=r.parameters)==null?void 0:x.docs)==null?void 0:f.source}}};var j,S,w;n.parameters={...n.parameters,docs:{...(j=n.parameters)==null?void 0:j.docs,source:{originalSource:`{
  args: {
    status: 'published'
  }
}`,...(w=(S=n.parameters)==null?void 0:S.docs)==null?void 0:w.source}}};var h,B,b;o.parameters={...o.parameters,docs:{...(h=o.parameters)==null?void 0:h.docs,source:{originalSource:`{
  args: {
    status: 'rejected'
  }
}`,...(b=(B=o.parameters)==null?void 0:B.docs)==null?void 0:b.source}}};var R,A,C;d.parameters={...d.parameters,docs:{...(R=d.parameters)==null?void 0:R.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">\r
      <StatusBadge status="draft" />\r
      <StatusBadge status="reviewing" />\r
      <StatusBadge status="approved" />\r
      <StatusBadge status="published" />\r
      <StatusBadge status="rejected" />\r
    </div>
}`,...(C=(A=d.parameters)==null?void 0:A.docs)==null?void 0:C.source}}};const q=["Draft","Reviewing","Approved","Published","Rejected","AllStatuses"];export{d as AllStatuses,r as Approved,t as Draft,n as Published,o as Rejected,a as Reviewing,q as __namedExportsOrder,P as default};
