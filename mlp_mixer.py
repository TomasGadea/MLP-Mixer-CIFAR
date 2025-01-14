import torch
import torch.nn as nn
import torch.nn.functional as F
from einops.layers.torch import Rearrange
import torchsummary


class MLPMixer(nn.Module):
    def __init__(self,in_channels=3,img_size=32, patch_size=4, hidden_size=512, hidden_s=256, hidden_c=2048, num_layers=8, num_classes=10, drop_p=0., off_act=False, is_cls_token=False):
        super(MLPMixer, self).__init__()
        num_patches = img_size // patch_size * img_size // patch_size
        # (b, c, h, w) -> (b, d, h//p, w//p) -> (b, h//p*w//p, d)
        self.is_cls_token = is_cls_token
        self.num_layers = num_layers

        self.patch_emb = nn.Sequential(
            nn.Conv2d(in_channels, hidden_size ,kernel_size=patch_size, stride=patch_size),
            Rearrange('b d h w -> b (h w) d')
        )

        if self.is_cls_token:
            self.cls_token = nn.Parameter(torch.randn(1, 1, hidden_size))
            num_patches += 1


        self.mixer_layers = nn.Sequential(
            *[
                MixerLayer(num_patches, hidden_size, hidden_s, hidden_c, drop_p, off_act) 
            for _ in range(num_layers)
            ]
        )
        self.ln = nn.LayerNorm(hidden_size)

        self.clf = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out = self.patch_emb(x)
        if self.is_cls_token:
            out = torch.cat([self.cls_token.repeat(out.size(0),1,1), out], dim=1)
        out = self.mixer_layers(out)
        out = self.ln(out)
        out = out[:, 0] if self.is_cls_token else out.mean(dim=1)
        out = self.clf(out)
        return out

    def L1L2_reg(self):
        """
        we get: torch.nn.parameter.Parameter
        c --> cell index
        i --> index in range 0..len(hidden_s_candidates)
        j --> index in range 0..len(hidden_c_candidates)

        model.cells[c].mlp1.mixed_op.ops[i][0].weight
        model.cells[c].mlp1.mixed_op.ops[i][3].weight

        model.cells[c].mlp2.mixed_op.ops[j][0].weight
        model.cells[c].mlp2.mixed_op.ops[j][3].weight

        """
        all_W = []
        for l in range(self.num_layers):
            all_W.append(self.mixer_layers[l].mlp1.fc1.weight)
            all_W.append(self.mixer_layers[l].mlp1.fc2.weight)
            all_W.append(self.mixer_layers[l].mlp2.fc1.weight)
            all_W.append(self.mixer_layers[l].mlp2.fc2.weight)
        all_W.append(self.clf.weight)

        row_reg = torch.cat([torch.norm(W, p=2, dim=1) for W in all_W])  # 1 x (L*H)
        reg = torch.norm(row_reg, p=1)  # 1 x 1
        return reg

    def friction(self):
        F = 0.
        for l in range(self.num_layers):
            F += self.mixer_layers[l].mlp1.fc1.out_features
            F += self.mixer_layers[l].mlp2.fc1.out_features
        return F


class MixerLayer(nn.Module):
    def __init__(self, num_patches, hidden_size, hidden_s, hidden_c, drop_p, off_act):
        super(MixerLayer, self).__init__()
        self.mlp1 = MLP1(num_patches, hidden_s, hidden_size, drop_p, off_act)
        self.mlp2 = MLP2(hidden_size, hidden_c, drop_p, off_act)
    def forward(self, x):
        out = self.mlp1(x)
        out = self.mlp2(out)
        return out

class MLP1(nn.Module):
    def __init__(self, num_patches, hidden_s, hidden_size, drop_p, off_act):
        super(MLP1, self).__init__()
        self.ln = nn.LayerNorm(hidden_size)
        self.T = Rearrange('b s c -> b c s')  # Transpose token and channel axis only
        self.fc1 = nn.Linear(num_patches, hidden_s)
        self.do1 = nn.Dropout(p=drop_p)
        self.fc2 = nn.Linear(hidden_s, num_patches)
        self.do2 = nn.Dropout(p=drop_p)
        self.act = F.gelu if not off_act else lambda x: x

    def forward(self, x):
        out = self.do1(self.act(self.fc1(self.T(self.ln(x)))))
        out = self.T(self.do2(self.fc2(out)))
        return out + x

class MLP2(nn.Module):
    def __init__(self, hidden_size, hidden_c, drop_p, off_act):
        super(MLP2, self).__init__()
        self.ln = nn.LayerNorm(hidden_size)
        self.fc1 = nn.Linear(hidden_size, hidden_c)
        self.do1 = nn.Dropout(p=drop_p)
        self.fc2 = nn.Linear(hidden_c, hidden_size)
        self.do2 = nn.Dropout(p=drop_p)
        self.act = F.gelu if not off_act else lambda x:x
    def forward(self, x):
        out = self.do1(self.act(self.fc1(self.ln(x))))
        out = self.do2(self.fc2(out))
        return out+x

if __name__ == '__main__':
    net = MLPMixer(
        in_channels=3,
        img_size=32, 
        patch_size=4, 
        hidden_size=128, 
        hidden_s=512, 
        hidden_c=64, 
        num_layers=8, 
        num_classes=10, 
        drop_p=0.,
        off_act=False,
        is_cls_token=True
        )
    torchsummary.summary(net, (3,32,32))
