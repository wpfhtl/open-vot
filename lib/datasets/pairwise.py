from __future__ import absolute_import

import numpy as np
from torch.utils.data import Dataset
from PIL import Image


class Pairwise(Dataset):

    def __init__(self, base_dataset, transform=None, pairs_per_video=25,
                 frame_range=100, causal=False, return_index=False,
                 rand_choice=True, subset='train', train_ratio=0.95):
        super(Pairwise, self).__init__()
        assert subset in ['train', 'val']

        self.base_dataset = base_dataset
        self.transform = transform
        self.pairs_per_video = pairs_per_video
        self.frame_range = frame_range
        self.causal = causal
        self.return_index = return_index
        self.rand_choice = rand_choice

        n = len(self.base_dataset)
        split = int(n * train_ratio)
        split = np.clip(split, 10, n - 10)
        if subset == 'train':
            self.indices = np.arange(0, split, dtype=int)
            self.indices = np.tile(self.indices, pairs_per_video)
        elif subset == 'val':
            self.indices = np.arange(split, n, dtype=int)

    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError('list index out of range')

        if self.rand_choice:
            index = np.random.choice(self.indices)
        else:
            index = self.indices[index]
        img_files, anno = self.base_dataset[index]

        rand_z, rand_x = self._sample_pair(len(img_files))
        img_z = Image.open(img_files[rand_z])
        img_x = Image.open(img_files[rand_x])
        if img_z.mode == 'L':
            img_z = img_z.convert('RGB')
            img_x = img_x.convert('RGB')
        bndbox_z = anno[rand_z, :]
        bndbox_x = anno[rand_x, :]

        if self.return_index:
            item = (img_z, img_x, bndbox_z, bndbox_x, rand_z, rand_x)
        else:
            item = (img_z, img_x, bndbox_z, bndbox_x)

        if self.transform is not None:
            return self.transform(*item)
        else:
            return item

    def __len__(self):
        return len(self.indices)

    def _sample_pair(self, n):
        if self.causal:
            rand_z = np.random.choice(n - 1)
        else:
            rand_z = np.random.choice(n)

        if self.frame_range == 0:
            return rand_z, rand_z

        possible_x = np.arange(
            rand_z - self.frame_range,
            rand_z + self.frame_range + 1)
        possible_x = np.intersect1d(possible_x, np.arange(n))
        if self.causal:
            possible_x = possible_x[possible_x > rand_z]
        else:
            possible_x = possible_x[possible_x != rand_z]
        rand_x = np.random.choice(possible_x)

        return rand_z, rand_x
