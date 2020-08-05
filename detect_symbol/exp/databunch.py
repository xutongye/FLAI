
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/databunch.ipynb

#================================================
from fastai.vision import *


#================================================
# 为ImageList类添加cache_image方法
def cache_image(self):
    cached_images = [self.open(fn) for fn in self.items]
    self.cached_images = cached_images

ImageList.cache_image = cache_image


#================================================
# 修改ImageList类的get方法
def get(self,i):
    if hasattr(self, 'cached_images'):
        res = self.cached_images[i]
    else:
        fn = super(ImageList, self).get(i)
        res = self.open(fn)

    self.sizes[i] = res.size
    return res

ImageList.get = get


#================================================
# 为 Databunch类添加cache_ds_img方法
def cache_ds_img(self):
    self.train_ds.x.cache_image()
    self.valid_ds.x.cache_image()

ImageDataBunch.cache_ds_img = cache_ds_img


#================================================
pat_coord = re.compile(r'\d+')
pat_clas = re.compile(r'\w+')
pat_imgName = re.compile(r'(\w+/\d+\.png)$')
kkk = 0
def get_label_from_df(fn, df, pat_imgName, box_col, cat_col):
    '''
    fn:
        file path.
    df:
        a dataframe stores all the label information, imageName shoud be as index.
    repat_imgName:
        a regular expression pattern, used to find the imageName from fn, where imageName is stored in df
    box_col:
        the column name of bounding boxs
    cat_col:
        the column name of categories
    '''
    pat_num = re.compile(r'\d+')
    pat_cat = re.compile(r'\w+')

    fn = pat_imgName.findall(fn)[0]

    boxes = df.loc[fn,box_col]
    boxes = pat_num.findall(boxes)
    boxes = list(map(np.long, boxes))
    boxes = np.array(boxes).reshape(-1,4)
    boxes = boxes.tolist()

    cats = df.loc[fn,cat_col]
    cats = pat_clas.findall(cats)

    assert len(boxes)==len(cats), 'length of bounding boxes and categories not equeal.'

    return (boxes,cats)


#================================================
@classmethod
def create(cls, h:int, w:int, bboxes:Collection[Collection[int]], labels:Collection=None, classes:dict=None,
           pad_idx:int=0, scale:bool=True)->'ImageBBox':
    "Create an ImageBBox object from `bboxes`."
    # the following 3 lines are added by xutongye
#     assert isinstance(bboxes,list) and isinstance(labels,list), 'bboxes and labels should be of type list.'
    if isinstance(bboxes,list) and len(bboxes)==0:
        bboxes = [[0,0,0,0]]
    # the code in fastai
    if isinstance(bboxes, np.ndarray) and bboxes.dtype == np.object: bboxes = np.array([bb for bb in bboxes])
    bboxes = tensor(bboxes).float()
    tr_corners = torch.cat([bboxes[:,0][:,None], bboxes[:,3][:,None]], 1)
    bl_corners = bboxes[:,1:3].flip(1)
    bboxes = torch.cat([bboxes[:,:2], tr_corners, bl_corners, bboxes[:,2:]], 1)
    flow = FlowField((h,w), bboxes.view(-1,2))
    return cls(flow, labels=labels, classes=classes, pad_idx=pad_idx, y_first=True, scale=scale)

ImageBBox.create = create


#================================================
def _compute_boxes(self) -> Tuple[LongTensor, LongTensor]:
    '''
    Check if there are bad bboxes (boxes whose area is zero). If there are, delete them.
    Bad boxes may be due to transformations, for example may rotate a bbox out of the image.
    Bad boxes may be added in the initial, because there indeed no object, but you has to add one, or there will be confilicts occur if you dont.
    '''
    bboxes = self.flow.flow.flip(1).view(-1, 4, 2).contiguous().clamp(min=-1, max=1)
    mins, maxes = bboxes.min(dim=1)[0], bboxes.max(dim=1)[0]
    bboxes = torch.cat([mins, maxes], 1)
    mask = (bboxes[:,2]-bboxes[:,0] > 0) * (bboxes[:,3]-bboxes[:,1] > 0)
    #if len(mask) == 0: return tensor([self.pad_idx] * 4), tensor([self.pad_idx])
    # 上句判断 len(mask)==0 是个bug
    if mask.sum()==0:
        return tensor([[self.pad_idx]*4]), tensor([self.pad_idx])
    res = bboxes[mask]
    if self.labels is None: return res,None
    return res, self.labels[to_np(mask).astype(bool)]

ImageBBox._compute_boxes = _compute_boxes


#================================================
def _rot90_affine(k:partial(uniform_int, 0, 3)):
    "Randomly rotate `x` image based on `k` as in np.rot90"
    if k%2 == 0:
        x = -1. if k&2 else 1.
        y = -1. if k&2 else 1.

        return [[x, 0, 0.],
                [0, y, 0],
                [0, 0, 1.]]
    else:
        x = 1. if k&2 else -1.
        y = -1. if k&2 else 1.

        return [[0, x, 0.],
                [y, 0, 0],
                [0, 0, 1.]]

rot90_affine = TfmAffine(_rot90_affine)


#================================================
def get_stats(data,dl_types=[DatasetType.Train]):
    '''
    根据一个databunch中的所有指定的（图片）数据来统计各通道的均值和标准差。
    --------------------------------
    参数：
    -- data：一个DataBunch对象
    -- dl_types：一个list，其元素可选自DatasetType.Train, DatasetType.Valid, DatasetType.Test
    --------------------------------
    返回值：
    -- mean：图片三个通道上的均值
    -- std：图片三个通道上的标准差
    '''
    tn,sm,ssm = 0,torch.zeros(3,device=data.device),torch.zeros(3,device=data.device) # tn: total number; sm: sum; ssm: square sum
    for dl_type in dl_types:
        dl = data.dl(dl_type)
        for x,_ in dl:
            tn += x.shape[0]
            sm += x.mean((0,2,3))*x.shape[0]
            ssm += x.pow(2).mean((0,2,3))*x.shape[0]

    mean = sm/tn
    std = (ssm/tn - mean.pow(2)).sqrt()

    return mean, std


#================================================
def databunch_statistics(data:DataBunch,show=True):
    train_ys = data.train_ds.y
    valid_ys = data.valid_ds.y

    hw_statistics = [[],[]]
    cat_statistics = [dict([(cla,0) for cla in data.train_dl.y.classes[1:]]),
                      dict([(cla,0) for cla in data.train_dl.y.classes[1:]])]

    for hw_stat,cat_stat,ys in zip(hw_statistics, cat_statistics, [train_ys,valid_ys]):
        for y in ys:
            if len(y.labels)==0: continue

            # 统计目标类别
            for clas in y.labels:
                cat_stat[clas.obj] += 1

            # 统计高宽
            pts = y.flow.flow
            pts = pts.reshape(-1,4,2)
            hws = pts.max(dim=1)[0] - pts.min(dim=1)[0]
            hw_stat += [hws]

    train_cat,valid_cat = cat_statistics
    train_hw,valid_hw = hw_statistics
    train_hw = torch.cat(train_hw,dim=0)
    valid_hw = torch.cat(valid_hw,dim=0)

    if show:


        # 显示各类别计数
        print('{:>41}{:>10}'.format('train','valid'))
        print('------------------------------------------------------')
        train_tot = 0
        valid_tot = 0
        for k,v in train_cat.items():
            valid_v = valid_cat[k]
            print('{:>30}:{:>10}{:>10}'.format(k,v,valid_v))
            train_tot += v
            valid_tot += valid_v
        print('------------------------------------------------------')
        print('{:>30}:{:>10}{:>10}'.format('total',train_tot,valid_tot))

        # 绘制高宽分布
        print('\n\n')
        print('red for train; blue for valid:')
        plt.scatter(train_hw[:,0],train_hw[:,1],c='r',marker='.',linewidths=2);
        plt.scatter(valid_hw[:,0],valid_hw[:,1],c='b',marker='.',linewidths=0);


    return train_hw, valid_hw, train_cat, valid_cat


#================================================
# 这个函数是为了在其它模块的设计时快速构造databunch
def get_databunch(data_root='./data/ds_20200227', csv_name='gends.csv', valid_pct=0.2, bs=64, device=torch.device('cpu'), cache=False):
    '''
    --------------------------------
    参数：
    -- data_root：数据集的总目录
    -- csv_name：存放标注信息的csv文件名，其要符合“对csv的要求”
    -- valid_pct：随机分割训练/验证集，该参数指定验证集的比例
    -- bs：batch size
    -- device：在datalaoder迭代时，dataloader先将batch加载到该device，做batch transform，然后返回。
    -- cache：dataset是否将所有图片预缓存入内存
    --------------------------------
    返回值：
    -- 一个databunch对象
    --------------------------------
    对csv的要求：
    1，带index
    2，存放图片名的列名称为"image"
    3，存放bbox信息的列名称为"box"
    4，存放类别信息的列名称为"cls"
    --------------------------------
    '''
    data_root = Path(data_root)
    csv_name = Path('gends.csv')
    # 读入csv，稍作处理，方便get_label函数操作
    csv_path = data_root/csv_name
    df = pd.read_csv(csv_path,index_col=0)
    df = df.set_index('image')

    # ItemList
    data = ObjectItemList.from_csv(path=data_root, csv_name=csv_name, cols='image')

    # split ItemList to get ItemLists
    data = data.split_by_rand_pct(valid_pct=valid_pct)

    # label ItemLists to get LabelLists
    pat_imgName = re.compile(r'(\w+/\d+\.jpg)$')
    func = partial(get_label_from_df, df=df, pat_imgName=pat_imgName, box_col='box', cat_col='cls')
    data = data.label_from_func(func=func)

    # add transforms
    trn_tfms = [*zoom_crop(scale=(0.9,1.1),do_rand=True,p=1),
                rot90_affine(use_on_y=True)]
    val_tfms = []

    data = data.transform(tfms=[trn_tfms,val_tfms], tfm_y=True, remove_out=True)

    # create DataBunch from LabelLists
    data = data.databunch(bs=bs, device=device, collate_fn=bb_pad_collate, num_workers=0)

    # normalize
    data = data.normalize()

    # 缓存图片
    if cache:
        data.cache_ds_img()

    return data