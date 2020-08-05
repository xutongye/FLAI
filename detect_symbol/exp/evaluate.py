
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/evaluate.ipynb

#================================================
def count(L):
    '''
    统计tensor中各元素出现的次数,返回一个字典，键为各元素，值为各元素出现的次数
    '''
    result = collections.defaultdict(int)
    if L is not None:
        for x in L:
            result[x.item()] += 1
    return result


#================================================
def get_TpFpFn(dl,model,n_clas,hit_thres,filt_thress,device,gaf):
    '''
    参数：
    --dl：一个dataloader，这是计算tpfpfn的数据集
    --model：模型
    --n_clas：类别数
    --hit_thres：预测框与目标框的IoU高于该值则认为该预测框击中（或称匹配）上了该目标
    --filt_thress：一列filt_threshold，得分高于该阈值的预测框才会参加 nms
    --device：torch.device对象
    --gaf：一个GridAnchor_Funcs对象（见exp/nb_anchors_loss_metrics.py）
    '''
    pd = torch.zeros((len(filt_thress),n_clas)) # prediction
    gt = torch.zeros((len(filt_thress),n_clas)) # ground truth
    tp = torch.zeros((len(filt_thress),n_clas)) # true positive

    # 遍历dl中的每个databunch
    mb = master_bar(dl)
    mb.main_bar.comment = 'batchs'
    for x,y in mb:
        # 模型做预测，并处理其输出
        netOut = model(x.to(device))

        # 由低到高遍历不同的filt_thres
        cb = progress_bar(filt_thress, parent=mb) # child bar
        mb.child.comment = 'filt_thress'
        for i,filt_thres in enumerate(cb):
            # pb: prediction batch
            pb_boxs, _, pb_cats, _, _ = nb_interpretation.netouts2preds(batchOut=netOut,
                                                                        gaf=gaf,
                                                                        composeConfPrb=True,
                                                                        filt_thres=filt_thres,
                                                                        ov_thres=0.2,
                                                                        despiteCat=True)
            # 遍历databunch中每一条数据
            for idx in range(0,x.shape[0]):
                p_boxs = pb_boxs[idx] # p: prediction
                p_cats = pb_cats[idx]

                if len(p_cats)>0:
                    count_pred = count(p_cats)
                    pred_cats = [k for k in count_pred.keys()]
                    pred_cnts = tensor([v for v in count_pred.values()])
                    pd[i][pred_cats] += pred_cnts

                gt_boxs,gt_clas = y[0][idx],y[1][idx] # gt: ground truch
                keep = nb_anchors_loss_metrics.get_y(gt_boxs)
                if len(keep)>0:
                    gt_boxs = gt_boxs[keep]
                    gt_clas = gt_clas[keep]
                    gt_boxs = (gt_boxs + 1) / 2
                    gt_clas = gt_clas - 1

                    count_gt = count(gt_clas)
                    gt_cats = [k for k in count_gt.keys()]
                    gt_cnts = tensor([v for v in count_gt.values()])
                    gt[i][gt_cats] += gt_cnts

                if len(keep)==0 or len(p_cats)==0:
                    continue


                #---------------------------------------------------------------------------------
                #-------- 击中匹配 ---------------------------------------------------------------
                #---------------------------------------------------------------------------------
                # 1. 计算IoU匹配矩阵
                ious = nb_anchors_loss_metrics.iou(p_boxs[:,None,:],gt_boxs[None,:,:])
                # 2. 仅保留IoU高于阈值的匹配
                ious = torch.where(ious > hit_thres, ious, tensor(0.,device=device))

                # 3. 仅保留类别一致的匹配
                mask_sameClas = (gt_clas[None,:]==p_cats[:,None])
                ious_sameClas = torch.where(mask_sameClas,ious,tensor(0.,device=device))

                # 4. 每个pred仅保留IoU最大的一个匹配，作为hit
                hit_yes = ious_sameClas.sum(axis=1)>0
                hit_who = torch.argmax(ious_sameClas,axis=1)
                hit_who = hit_who[hit_yes]

                if len(hit_who)==0:
                    continue

                # 5. 统计被击中的gt，即使被多次击中也只统计一次
                who_isHit = tensor(list(set(hit_who)))
                who_isHit = gt_clas[who_isHit]

                # 6. 统计
                count_tp = count(who_isHit)
                tp_cats = [k for k in count_tp.keys()]
                tp_cnts = tensor([v for v in count_tp.values()])
                tp[i][tp_cats] += tp_cnts

    fp = pd - tp
    fn = gt - tp

    return tp, fp, fn, pd, gt
